from pathlib import Path

from codepilot.cli import save_code


def test_save_code_writes_only_the_implementation(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    code_path = save_code("Write a helper function", "def helper():\n    return 1")
    saved_path = tmp_path / code_path

    assert code_path == Path("generated") / "write_a_helper_function.py"
    assert saved_path.read_text(encoding="utf-8") == "def helper():\n    return 1\n"
    assert list((tmp_path / "generated").iterdir()) == [saved_path]
