"""TUI Widgets and Components."""

from typing import Dict, Any, List, Optional
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.layout import Layout
from rich.columns import Columns
from rich.align import Align
from ..tui.config import TUIConfig


class StatusWidget:
    """Widget for displaying application status."""

    def __init__(self, config: TUIConfig):
        self.config = config
        self.console = config.get_console()

    def render(self, status_info: Dict[str, Any]) -> Panel:
        """Render status information."""
        lines = []

        # Provider status
        provider = status_info.get("provider", "unknown")
        model = status_info.get("model", "unknown")
        lines.append(f"[bold]Provider:[/bold] {provider} ({model})")

        # Session info
        session_count = status_info.get("session_count", 0)
        current_session = status_info.get("current_session")
        lines.append(f"[bold]Sessions:[/bold] {session_count}")
        if current_session:
            lines.append(f"[bold]Current:[/bold] {current_session}")

        # Health status
        health = status_info.get("health", {})
        health_text = []
        for service, status in health.items():
            icon = "✅" if status == "healthy" else "❌"
            health_text.append(f"{icon} {service}")
        lines.append(f"[bold]Health:[/bold] {' | '.join(health_text)}")

        content = "\n".join(lines)
        return Panel(content, title="Status", style="blue")


class SessionWidget:
    """Widget for displaying chat sessions."""

    def __init__(self, config: TUIConfig):
        self.config = config
        self.console = config.get_console()

    def render(self, session: Optional[Dict[str, Any]] = None) -> Panel:
        """Render session content."""
        if not session:
            return Panel("No active session", style="dim")

        messages = session.get("messages", [])
        if not messages:
            return Panel("Empty session - start chatting!", style="dim")

        # Display last few messages
        display_messages = messages[-10:]  # Show last 10 messages

        message_panels = []
        for msg in display_messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", 0)

            # Format timestamp
            if self.config.show_timestamps:
                import time
                time_str = time.strftime("%H:%M:%S", time.localtime(timestamp))
                header = f"{role.title()} ({time_str})"
            else:
                header = role.title()

            # Style based on role and error status
            style = "green" if role == "assistant" else "blue"
            if msg.get("is_error"):
                style = "red"

            # Word wrap content if enabled
            if self.config.word_wrap and len(content) > self.config.max_line_length:
                import textwrap
                content = "\n".join(textwrap.wrap(content, width=self.config.max_line_length))

            message_panel = Panel(
                content,
                title=header,
                style=style,
                title_align="left"
            )
            message_panels.append(message_panel)

        # Combine all messages
        content = Group(*message_panels)
        return Panel(content, title=f"Session: {session.get('id', 'unknown')}", style="white")


class ChatWidget:
    """Widget for chat input and interaction."""

    def __init__(self, config: TUIConfig):
        self.config = config
        self.console = config.get_console()
        self.input_buffer = ""

    def render_input(self) -> Panel:
        """Render input area."""
        if self.input_buffer:
            content = f"> {self.input_buffer}"
        else:
            content = "> Type your message here..."

        return Panel(content, title="Input", style="cyan")

    def add_char(self, char: str) -> None:
        """Add character to input buffer."""
        self.input_buffer += char

    def delete_char(self) -> None:
        """Delete character from input buffer."""
        self.input_buffer = self.input_buffer[:-1]

    def clear_input(self) -> None:
        """Clear input buffer."""
        self.input_buffer = ""

    def get_input(self) -> str:
        """Get current input."""
        return self.input_buffer

    def set_input(self, text: str) -> None:
        """Set input buffer."""
        self.input_buffer = text


class MenuWidget:
    """Widget for displaying menus."""

    def __init__(self, config: TUIConfig):
        self.config = config
        self.console = config.get_console()

    def render_main_menu(self) -> Panel:
        """Render main menu."""
        menu_items = [
            "[bold cyan]Main Menu[/bold cyan]",
            "",
            "[green]n[/green] - New Session",
            "[green]s[/green] - Settings",
            "[green]l[/green] - List Sessions",
            "[green]h[/green] - Help",
            "[green]q[/green] - Quit",
            "",
            "[dim]Select an option or press the corresponding key[/dim]"
        ]

        content = "\n".join(menu_items)
        return Panel(content, title="Literacy Coach TUI", style="blue")

    def render_help(self) -> Panel:
        """Render help information."""
        help_items = [
            "[bold cyan]Help & Shortcuts[/bold cyan]",
            "",
            "[bold]Navigation:[/bold]",
            "• [green]Tab[/green] - Switch panels",
            "• [green]Arrow keys[/green] - Navigate",
            "• [green]Enter[/green] - Select",
            "",
            "[bold]Chat:[/bold]",
            "• [green]Type[/green] - Enter message",
            "• [green]Ctrl+C[/green] - Cancel input",
            "• [green]Ctrl+L[/green] - Clear screen",
            "",
            "[bold]Sessions:[/bold]",
            "• [green]n[/green] - New session",
            "• [green]Ctrl+N[/green] - Next session",
            "• [green]Ctrl+P[/green] - Previous session",
            "",
            "[bold]General:[/bold]",
            "• [green]q[/green] - Quit",
            "• [green]?[/green] - This help",
            "• [green]r[/green] - Refresh",
        ]

        content = "\n".join(help_items)
        return Panel(content, title="Help", style="green")


class ProgressWidget:
    """Widget for displaying progress bars."""

    def __init__(self, config: TUIConfig):
        self.config = config
        self.console = config.get_console()

    def render_progress(self, title: str, progress: float, status: str = "") -> Panel:
        """Render a progress bar."""
        from rich.progress import Progress, TaskID

        progress_bar = Progress()
        task = progress_bar.add_task(title, total=100)

        # Update progress
        progress_bar.update(task, completed=int(progress * 100))

        content = progress_bar
        if status:
            content = Group(progress_bar, Text(status, style="dim"))

        return Panel(content, title="Progress", style="yellow")


class TableWidget:
    """Widget for displaying tabular data."""

    def __init__(self, config: TUIConfig):
        self.config = config
        self.console = config.get_console()

    def render_sessions_table(self, sessions: List[Dict[str, Any]]) -> Panel:
        """Render sessions as a table."""
        table = Table(title="Chat Sessions", show_header=True, header_style="bold magenta")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Type", style="green")
        table.add_column("Messages", style="yellow", justify="right")
        table.add_column("Created", style="white")

        for session in sessions[-10:]:  # Show last 10 sessions
            import time
            created_time = time.strftime(
                "%Y-%m-%d %H:%M",
                time.localtime(session.get("created_at", 0))
            )

            table.add_row(
                session.get("id", "unknown")[:8] + "...",
                session.get("type", "unknown"),
                str(len(session.get("messages", []))),
                created_time
            )

        return Panel(table, style="white")

    def render_models_table(self, models: List[Dict[str, Any]]) -> Panel:
        """Render available models as a table."""
        table = Table(title="Available Models", show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan")
        table.add_column("Size", style="green", justify="right")
        table.add_column("Modified", style="white")

        for model in models:
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
                modified = time.strftime("%Y-%m-%d %H:%M", time.localtime(modified))

            table.add_row(
                model.get("name", "unknown"),
                size,
                modified
            )

        return Panel(table, style="white")