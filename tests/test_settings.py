import pytest
from dotenv import dotenv_values

from codepilot import settings


def test_user_config_file_uses_xdg_config_home(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))

    assert settings.user_config_file() == tmp_path / "config" / "codepilot" / ".env"


def test_save_api_key_writes_private_env_file(monkeypatch, tmp_path):
    config_file = tmp_path / "codepilot" / ".env"
    monkeypatch.setattr(settings, "user_config_file", lambda: config_file)

    saved_file = settings.save_api_key("  secret-key  ")

    assert saved_file == config_file
    assert dotenv_values(config_file)["OPENAI_API_KEY"] == "secret-key"
    assert config_file.stat().st_mode & 0o777 == 0o600


def test_save_api_key_rejects_empty_value(monkeypatch, tmp_path):
    config_file = tmp_path / ".env"
    monkeypatch.setattr(settings, "user_config_file", lambda: config_file)

    with pytest.raises(ValueError, match="cannot be empty"):
        settings.save_api_key("  ")

    assert not config_file.exists()


def test_load_configuration_prefers_user_key_to_project_dotenv(
    monkeypatch,
    tmp_path,
):
    user_env = tmp_path / "user.env"
    project_env = tmp_path / ".env"
    user_env.write_text("OPENAI_API_KEY=saved-key\n", encoding="utf-8")
    project_env.write_text("OPENAI_API_KEY=project-key\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(settings, "user_config_file", lambda: user_env)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    settings.load_configuration()

    assert settings.os.environ["OPENAI_API_KEY"] == "saved-key"
