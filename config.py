"""
config.py — Central configuration for linkr-bot.
Reads from environment variables / .env file.
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Set
from dotenv import load_dotenv

load_dotenv()


def _parse_ids(value: str) -> Set[int]:
    """Parse comma-separated Telegram user IDs."""
    return {int(x.strip()) for x in value.split(",") if x.strip()}


@dataclass
class Config:
    # ── Telegram ──────────────────────────────────────────────
    bot_token: str = field(default_factory=lambda: os.getenv("BOT_TOKEN", ""))
    bot_api_url: str = field(
        default_factory=lambda: os.getenv("BOT_API_URL", "https://api.telegram.org")
    )
    concurrent_updates: int = field(
        default_factory=lambda: int(os.getenv("CONCURRENT_UPDATES", "30"))
    )

    # ── GoFile ────────────────────────────────────────────────
    gofile_token: Optional[str] = field(
        default_factory=lambda: os.getenv("GOFILE_TOKEN")
    )

    # ── Storage ───────────────────────────────────────────────
    temp_dir: str = field(
        default_factory=lambda: os.getenv("TEMP_DIR", "/tmp/linkr-bot")
    )
    db_path: str = field(
        default_factory=lambda: os.getenv("DB_PATH", "linkr_bot.db")
    )

    # ── Limits ────────────────────────────────────────────────
    max_file_size_mb: int = field(
        default_factory=lambda: int(os.getenv("MAX_FILE_SIZE", "50"))
    )

    # ── Defaults ──────────────────────────────────────────────
    default_language: str = field(
        default_factory=lambda: os.getenv("DEFAULT_LANGUAGE", "en")
    )

    # ── Access control ────────────────────────────────────────
    whitelist_raw: str = field(
        default_factory=lambda: os.getenv("WHITELIST", "")
    )
    admins_raw: str = field(
        default_factory=lambda: os.getenv("ADMINS", "")
    )

    # ── Misc ──────────────────────────────────────────────────
    log_level: str = field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper()
    )
    repo_url: str = field(
        default_factory=lambda: os.getenv(
            "REPO_URL", "https://github.com/IIDZII-Dev/linkr-bot"
        )
    )

    # ── Computed ──────────────────────────────────────────────
    @property
    def whitelist(self) -> Set[int]:
        return _parse_ids(self.whitelist_raw) if self.whitelist_raw else set()

    @property
    def admins(self) -> Set[int]:
        return _parse_ids(self.admins_raw) if self.admins_raw else set()

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admins

    def is_allowed(self, user_id: int) -> bool:
        if not self.whitelist:
            return True
        return user_id in self.whitelist or user_id in self.admins


# Singleton
cfg = Config()