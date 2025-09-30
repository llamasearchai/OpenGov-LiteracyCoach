"""Main TUI Application."""

import asyncio
import os
import sys
from typing import Optional, Dict, Any
from pathlib import Path

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from .config import TUIConfig
from .menus import MainMenu
from .widgets import StatusWidget, SessionWidget
from ..services.ollama_client import OllamaClient
from ..services.openai_client import get_client as get_openai_client


class TUIApp:
    """Main Terminal User Interface Application."""

    def __init__(self):
        self.config = TUIConfig.load()
        self.console = self.config.get_console()
        self.layout = Layout()

        # Initialize clients
        self.ollama_client = OllamaClient(self.config.ollama_base_url)
        self.openai_client = None
        if self.config.openai_api_key:
            os.environ["OPENAI_API_KEY"] = self.config.openai_api_key
            self.openai_client = get_openai_client()

        # Application state
        self.current_session: Optional[Dict[str, Any]] = None
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.is_running = False

        # Widgets
        self.status_widget = StatusWidget(self.config)
        self.session_widget: Optional[SessionWidget] = None

        # Load existing sessions
        self._load_sessions()

    def _load_sessions(self) -> None:
        """Load existing sessions from storage."""
        sessions_dir = Path(self.config.data_dir) / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)

        for session_file in sessions_dir.glob("*.json"):
            try:
                with open(session_file, "r") as f:
                    session_data = json.load(f)
                self.sessions[session_data["id"]] = session_data
            except Exception:
                pass

    def _save_session(self, session_id: str) -> None:
        """Save session to storage."""
        if session_id not in self.sessions:
            return

        sessions_dir = Path(self.config.data_dir) / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)

        session_file = sessions_dir / f"{session_id}.json"
        with open(session_file, "w") as f:
            json.dump(self.sessions[session_id], f, indent=2)

    def create_session(self, session_type: str = "chat") -> str:
        """Create a new session."""
        import uuid
        session_id = str(uuid.uuid4())

        self.current_session = {
            "id": session_id,
            "type": session_type,
            "messages": [],
            "created_at": asyncio.get_event_loop().time(),
            "metadata": {}
        }
        self.sessions[session_id] = self.current_session
        return session_id

    def get_current_session(self) -> Optional[Dict[str, Any]]:
        """Get current session."""
        return self.current_session

    def switch_session(self, session_id: str) -> bool:
        """Switch to a different session."""
        if session_id in self.sessions:
            self.current_session = self.sessions[session_id]
            return True
        return False

    async def send_message(self, message: str) -> str:
        """Send a message and get response."""
        if not self.current_session:
            return "No active session. Create a session first."

        # Add user message
        user_message = {
            "role": "user",
            "content": message,
            "timestamp": asyncio.get_event_loop().time()
        }
        self.current_session["messages"].append(user_message)

        try:
            # Get response based on provider
            if self.config.default_llm_provider == "ollama":
                response = await self.ollama_client.chat_completion(
                    self.current_session["messages"],
                    model=self.config.default_model
                )
            elif self.config.default_llm_provider == "openai" and self.openai_client:
                response = await self._openai_chat_completion(
                    self.current_session["messages"]
                )
            else:
                return "No LLM provider available."

            # Add assistant response
            assistant_message = {
                "role": "assistant",
                "content": response,
                "timestamp": asyncio.get_event_loop().time()
            }
            self.current_session["messages"].append(assistant_message)

            # Auto-save if enabled
            if self.config.auto_save_sessions:
                self._save_session(self.current_session["id"])

            return response

        except Exception as e:
            error_msg = f"Error getting response: {str(e)}"
            # Add error message
            error_message = {
                "role": "assistant",
                "content": error_msg,
                "timestamp": asyncio.get_event_loop().time(),
                "is_error": True
            }
            self.current_session["messages"].append(error_message)
            return error_msg

    async def _openai_chat_completion(self, messages: list) -> str:
        """Get completion from OpenAI."""
        if not self.openai_client:
            raise RuntimeError("OpenAI client not initialized")

        # Convert messages to OpenAI format
        openai_messages = []
        for msg in messages:
            openai_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        response = self.openai_client.chat.completions.create(
            model=self.config.default_model,
            messages=openai_messages,
            temperature=0.7,
            max_tokens=1000
        )

        return response.choices[0].message.content

    def get_status_text(self) -> str:
        """Get current status text."""
        provider = self.config.default_llm_provider
        model = self.config.default_model
        session_count = len(self.sessions)
        current_session_id = self.current_session["id"] if self.current_session else None

        return f"Provider: {provider} | Model: {model} | Sessions: {session_count} | Current: {current_session_id}"

    def update_layout(self) -> Layout:
        """Update the application layout."""
        # Header
        header_text = Text("OpenGov Literacy Coach TUI", style="bold bright_blue")
        header = Panel(header_text, style="blue")

        # Status bar
        status_text = Text(self.get_status_text(), style="dim")
        status_bar = Panel(status_text, style="dim blue")

        # Main content area
        if self.current_session and self.session_widget:
            main_content = self.session_widget.render()
        else:
            main_content = Panel("No active session. Press 'n' to create a new session.", style="dim")

        # Combine layout
        self.layout.split_column(
            Layout(header, size=3),
            Layout(main_content, name="main"),
            Layout(status_bar, size=3)
        )

        return self.layout

    async def run(self) -> None:
        """Run the TUI application."""
        self.is_running = True

        # Initialize session widget
        self.session_widget = SessionWidget(self.config)

        with Live(self.update_layout(), console=self.console, refresh_per_second=4) as live:
            while self.is_running:
                try:
                    # Update layout
                    live.update(self.update_layout())

                    # Handle input (simplified - in real implementation would use keyboard library)
                    await asyncio.sleep(0.1)

                except KeyboardInterrupt:
                    break
                except Exception as e:
                    self.console.print(f"[red]Error:[/red] {str(e)}")

        self.console.print("Goodbye!")

    def quit(self) -> None:
        """Quit the application."""
        self.is_running = False

        # Save current session if needed
        if self.current_session and self.config.auto_save_sessions:
            self._save_session(self.current_session["id"])

        # Save configuration
        self.config.save()


def main():
    """Main entry point for TUI."""
    app = TUIApp()
    asyncio.run(app.run())


if __name__ == "__main__":
    main()