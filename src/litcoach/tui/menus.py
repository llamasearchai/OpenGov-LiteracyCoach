"""TUI Menu System."""

from typing import Dict, Any, List, Optional, Callable
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
from rich.align import Align
from ..tui.config import TUIConfig


class MenuItem:
    """Represents a menu item."""

    def __init__(self, key: str, label: str, description: str, action: Optional[Callable] = None):
        self.key = key
        self.label = label
        self.description = description
        self.action = action

    def render(self) -> Text:
        """Render the menu item."""
        return Text(f"[{self.key}] {self.label} - {self.description}")


class MainMenu:
    """Main menu for the TUI application."""

    def __init__(self, config: TUIConfig):
        self.config = config
        self.console = config.get_console()
        self.items = self._create_menu_items()

    def _create_menu_items(self) -> List[MenuItem]:
        """Create main menu items."""
        return [
            MenuItem("n", "New Session", "Start a new chat session"),
            MenuItem("l", "List Sessions", "View and manage existing sessions"),
            MenuItem("s", "Settings", "Configure application settings"),
            MenuItem("m", "Models", "Manage LLM models"),
            MenuItem("h", "Help", "Show help and shortcuts"),
            MenuItem("q", "Quit", "Exit the application"),
        ]

    def render(self) -> Panel:
        """Render the main menu."""
        title = Text("OpenGov Literacy Coach TUI", style="bold bright_blue", justify="center")

        menu_items = [title, Text("")]

        for item in self.items:
            menu_items.append(item.render())

        menu_items.extend([
            Text(""),
            Text("Press the key for your choice, or use arrow keys to navigate", style="dim italic")
        ])

        content = Group(*menu_items)
        return Panel(
            content,
            title="Main Menu",
            style="blue",
            title_align="center"
        )

    def get_item_by_key(self, key: str) -> Optional[MenuItem]:
        """Get menu item by key."""
        for item in self.items:
            if item.key == key:
                return item
        return None


class SessionMenu:
    """Menu for session management."""

    def __init__(self, config: TUIConfig, sessions: List[Dict[str, Any]]):
        self.config = config
        self.console = config.get_console()
        self.sessions = sessions

    def render(self) -> Panel:
        """Render session management menu."""
        if not self.sessions:
            content = Text("No sessions found. Create a new session to get started.", style="dim")
            return Panel(content, title="Sessions", style="yellow")

        # Create table of sessions
        table = Table(title="Chat Sessions", show_header=True, header_style="bold magenta")
        table.add_column("ID", style="cyan", no_wrap=True, max_width=10)
        table.add_column("Type", style="green", max_width=10)
        table.add_column("Messages", style="yellow", justify="right", max_width=8)
        table.add_column("Created", style="white", max_width=15)
        table.add_column("Preview", style="dim", max_width=30)

        for session in self.sessions[-20:]:  # Show last 20 sessions
            import time

            # Format creation time
            created_time = time.strftime(
                "%m/%d %H:%M",
                time.localtime(session.get("created_at", 0))
            )

            # Get preview of last message
            messages = session.get("messages", [])
            preview = ""
            if messages:
                last_msg = messages[-1]
                preview = last_msg.get("content", "")[:27] + "..."

            table.add_row(
                session.get("id", "unknown")[:8] + "...",
                session.get("type", "unknown"),
                str(len(messages)),
                created_time,
                preview
            )

        # Add action hints
        hints = Text("\n[dim]Actions: [green]Enter[/green] - Select session, [green]d[/green] - Delete session, [green]q[/green] - Back[/dim]")

        content = Group(table, hints)
        return Panel(content, title="Session Management", style="white")


class SettingsMenu:
    """Menu for application settings."""

    def __init__(self, config: TUIConfig):
        self.config = config
        self.console = config.get_console()
        self.categories = self._create_categories()

    def _create_categories(self) -> Dict[str, List[MenuItem]]:
        """Create settings categories."""
        return {
            "LLM Settings": [
                MenuItem("p", "Provider", f"Current: {self.config.default_llm_provider}"),
                MenuItem("m", "Model", f"Current: {self.config.default_model}"),
                MenuItem("u", "Ollama URL", f"Current: {self.config.ollama_base_url}"),
                MenuItem("k", "OpenAI Key", "Set OpenAI API key" if not self.config.openai_api_key else "Update OpenAI API key"),
            ],
            "UI Settings": [
                MenuItem("t", "Theme", f"Current: {self.config.theme_name}"),
                MenuItem("w", "Word Wrap", f"Current: {self.config.word_wrap}"),
                MenuItem("l", "Line Length", f"Current: {self.config.max_line_length}"),
                MenuItem("s", "Show Timestamps", f"Current: {self.config.show_timestamps}"),
            ],
            "Session Settings": [
                MenuItem("h", "Max History", f"Current: {self.config.max_session_history}"),
                MenuItem("a", "Auto Save", f"Current: {self.config.auto_save_sessions}"),
                MenuItem("o", "Timeout", f"Current: {self.config.session_timeout}s"),
            ]
        }

    def render(self) -> Panel:
        """Render settings menu."""
        title = Text("Settings", style="bold bright_blue", justify="center")

        content_parts = [title, Text("")]

        for category, items in self.categories.items():
            # Category header
            content_parts.append(Text(f"[bold cyan]{category}:[/bold cyan]"))
            content_parts.append(Text(""))

            # Category items
            for item in items:
                content_parts.append(item.render())

            content_parts.append(Text(""))

        content_parts.extend([
            Text("[dim]Press key to edit setting, or [green]q[/green] to go back[/dim]")
        ])

        content = Group(*content_parts)
        return Panel(content, title="Settings", style="blue")

    def get_item_by_key(self, key: str) -> Optional[MenuItem]:
        """Get menu item by key across all categories."""
        for category_items in self.categories.values():
            for item in category_items:
                if item.key == key:
                    return item
        return None


class ModelMenu:
    """Menu for model management."""

    def __init__(self, config: TUIConfig, available_models: List[Dict[str, Any]]):
        self.config = config
        self.console = config.get_console()
        self.available_models = available_models

    def render(self) -> Panel:
        """Render model management menu."""
        if not self.available_models:
            content = Text("No models available. Install models using 'ollama pull <model-name>'", style="yellow")
            return Panel(content, title="Models", style="yellow")

        # Create table of models
        table = Table(title="Available Models", show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan")
        table.add_column("Size", style="green", justify="right")
        table.add_column("Modified", style="white")
        table.add_column("Status", style="yellow")

        for model in self.available_models:
            # Format size
            size_bytes = model.get("size", 0)
            if size_bytes > 1024 * 1024 * 1024:
                size = f"{size_bytes / (1024*1024*1024)".1f"}GB"
            elif size_bytes > 1024 * 1024:
                size = f"{size_bytes / (1024*1024)".1f"}MB"
            else:
                size = f"{size_bytes / 1024".1f"}KB"

            # Format modified time
            modified = model.get("modified_at", "unknown")
            if modified != "unknown":
                import time
                modified = time.strftime("%Y-%m-%d", time.localtime(modified))

            # Status
            status = "✅ Ready" if model.get("name") == self.config.default_model else "⭕ Available"

            table.add_row(
                model.get("name", "unknown"),
                size,
                modified,
                status
            )

        # Add action hints
        current = f"Current: {self.config.default_model}"
        hints = Text(f"\n[dim]{current} | Actions: [green]Enter[/green] - Select model, [green]p[/green] - Pull new model, [green]q[/green] - Back[/dim]")

        content = Group(table, hints)
        return Panel(content, title="Model Management", style="white")


class HelpMenu:
    """Menu for displaying help information."""

    def __init__(self, config: TUIConfig):
        self.config = config
        self.console = config.get_console()

    def render(self) -> Panel:
        """Render help menu."""
        help_sections = [
            ("[bold cyan]Navigation[/bold cyan]", [
                "• [green]Tab[/green] - Switch between panels",
                "• [green]Arrow Keys[/green] - Navigate menus",
                "• [green]Enter[/green] - Select/Confirm",
                "• [green]Esc[/green] - Go back/Cancel",
            ]),
            ("[bold cyan]Chat Interface[/bold cyan]", [
                "• [green]Type[/green] - Enter your message",
                "• [green]Ctrl+C[/green] - Cancel current input",
                "• [green]Ctrl+L[/green] - Clear screen",
                "• [green]Ctrl+S[/green] - Save session",
            ]),
            ("[bold cyan]Session Management[/bold cyan]", [
                "• [green]n[/green] - Create new session",
                "• [green]Ctrl+N[/green] - Next session",
                "• [green]Ctrl+P[/green] - Previous session",
                "• [green]d[/green] - Delete current session",
            ]),
            ("[bold cyan]General[/bold cyan]", [
                "• [green]q[/green] - Quit application",
                "• [green]?[/green] - Show this help",
                "• [green]r[/green] - Refresh display",
                "• [green]s[/green] - Open settings",
            ])
        ]

        content_parts = [Text("OpenGov Literacy Coach TUI - Help", style="bold bright_blue", justify="center"), Text("")]

        for title, items in help_sections:
            content_parts.append(Text(title))
            for item in items:
                content_parts.append(Text(f"  {item}"))
            content_parts.append(Text(""))

        content_parts.append(Text("[dim]Press any key to return to the main interface[/dim]"))

        content = Group(*content_parts)
        return Panel(content, title="Help", style="green")