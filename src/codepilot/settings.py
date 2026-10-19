import os
from pathlib import Path

from dotenv import load_dotenv, set_key


def user_config_file() -> Path:
    """Return the per-user .env file used by installed CodePilot commands."""
    config_root = (
        os.getenv("XDG_CONFIG_HOME")
        or os.getenv("APPDATA")
        or str(Path.home() / ".config")
    )
    return Path(config_root) / "codepilot" / ".env"


def load_configuration() -> None:
    """Load user settings first, then fall back to a project-local .env file."""
    load_dotenv(user_config_file())
    load_dotenv(Path.cwd() / ".env")


def save_api_key(api_key: str) -> Path:
    """Save the API key to the private per-user configuration file."""
    api_key = api_key.strip()
    if not api_key:
        raise ValueError("The API key cannot be empty.")

    config_file = user_config_file()
    config_file.parent.mkdir(parents=True, exist_ok=True)
    set_key(
        str(config_file),
        "OPENAI_API_KEY",
        api_key,
        quote_mode="always",
    )
    config_file.chmod(0o600)
    return config_file
