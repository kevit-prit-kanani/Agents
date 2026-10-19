from pathlib import Path

from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.document import Document

from codepilot.cli import (
    SlashCommandCompleter,
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
