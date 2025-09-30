"""TUI Configuration Management."""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from rich.console import Console
from rich.theme import Theme


@dataclass
class TUIConfig:
    """Configuration for the TUI application."""

    # Theme settings
    theme_name: str = "default"
    primary_color: str = "blue"
    secondary_color: str = "cyan"

    # LLM settings
    default_llm_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    openai_api_key: Optional[str] = None
    default_model: str = "llama3"

    # Session settings
    max_session_history: int = 50
    auto_save_sessions: bool = True
    session_timeout: int = 3600  # seconds

    # UI settings
    show_timestamps: bool = True
    word_wrap: bool = True
    max_line_length: int = 100

    # Data settings
    data_dir: str = "./data/tui"
    cache_dir: str = "./data/tui/cache"

    # Keybindings
    quit_key: str = "q"
    help_key: str = "?"
    new_session_key: str = "n"
    settings_key: str = "s"

    @classmethod
    def load(cls) -> "TUIConfig":
        """Load configuration from file."""
        config_path = Path.home() / ".literacy-coach" / "tui.json"

        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    data = json.load(f)
                return cls(**data)
            except Exception:
                pass

        return cls()

    def save(self) -> None:
        """Save configuration to file."""
        config_path = Path.home() / ".literacy-coach"
        config_path.mkdir(parents=True, exist_ok=True)

        config_file = config_path / "tui.json"
        with open(config_file, "w") as f:
            json.dump(asdict(self), f, indent=2)

    def get_rich_theme(self) -> Theme:
        """Get Rich theme based on configuration."""
        colors = {
            "default": {
                "primary": "bright_blue",
                "secondary": "bright_cyan",
                "success": "bright_green",
                "warning": "bright_yellow",
                "error": "bright_red",
                "info": "bright_white"
            },
            "dark": {
                "primary": "cyan",
                "secondary": "blue",
                "success": "green",
                "warning": "yellow",
                "error": "red",
                "info": "white"
            },
            "light": {
                "primary": "dark_blue",
                "secondary": "dark_cyan",
                "success": "dark_green",
                "warning": "dark_orange",
                "error": "red",
                "info": "black"
            }
        }

        theme_colors = colors.get(self.theme_name, colors["default"])
        return Theme(theme_colors)

    def get_console(self) -> Console:
        """Get configured Rich console."""
        return Console(theme=self.get_rich_theme())

    def update_from_dict(self, updates: Dict[str, Any]) -> None:
        """Update configuration from dictionary."""
        for key, value in updates.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def validate(self) -> list[str]:
        """Validate configuration and return list of issues."""
        issues = []

        if not self.ollama_base_url.startswith(("http://", "https://")):
            issues.append("Ollama base URL must start with http:// or https://")

        if self.max_session_history < 1:
            issues.append("Max session history must be at least 1")

        if self.session_timeout < 60:
            issues.append("Session timeout must be at least 60 seconds")

        if self.max_line_length < 50:
            issues.append("Max line length must be at least 50")

        return issues