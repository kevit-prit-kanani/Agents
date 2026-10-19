from pathlib import Path

from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.document import Document
from typer.testing import CliRunner

from codepilot.cli import (
    SlashCommandCompleter,
    app,
    handle_slash_command,
    save_code,
)


def test_save_code_writes_only_the_implementation(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    code_path = save_code("Write a helper function", "def helper():\n    return 1")
    saved_path = tmp_path / code_path

    assert code_path == Path("generated") / "write_a_helper_function.py"
    assert saved_path.read_text(encoding="utf-8") == "def helper():\n    return 1\n"
    assert list((tmp_path / "generated").iterdir()) == [saved_path]


def test_slash_completer_suggests_matching_commands():
    completer = SlashCommandCompleter()

    suggestions = list(
        completer.get_completions(Document("/"), CompleteEvent())
    )

    assert [suggestion.text for suggestion in suggestions] == [
        "/help",
        "/exit",
        "/quit",
    ]

    partial_matches = list(
        completer.get_completions(Document("/q"), CompleteEvent())
    )
    assert [suggestion.text for suggestion in partial_matches] == ["/quit"]


def test_slash_completer_does_not_suggest_for_regular_text():
    completer = SlashCommandCompleter()

    suggestions = list(
        completer.get_completions(Document("hello"), CompleteEvent())
    )

    assert suggestions == []


def test_only_slash_exit_commands_exit_chat():
    assert handle_slash_command("/exit") is True
    assert handle_slash_command("/QUIT") is True
    assert handle_slash_command("exit") is None
    assert handle_slash_command("quit") is None


def test_setup_command_saves_key_without_printing_it(monkeypatch, tmp_path):
    config_file = tmp_path / "codepilot" / ".env"
    monkeypatch.setattr(
        "codepilot.cli.save_api_key",
        lambda api_key: _save_key(config_file, api_key),
    )
    result = CliRunner().invoke(app, ["setup"], input="secret-key\nsecret-key\n")

    assert result.exit_code == 0
    assert "API key saved" in result.output
    assert "secret-key" not in result.output
    assert "secret-key" in config_file.read_text(encoding="utf-8")


def _save_key(config_file: Path, api_key: str) -> Path:
    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_file.write_text(f"OPENAI_API_KEY={api_key}\n", encoding="utf-8")
    return config_file
