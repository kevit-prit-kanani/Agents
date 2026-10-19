from types import SimpleNamespace

import pytest

import codepilot.agent as agent_module
from codepilot.agent import CodeAgent


class FakeResponses:
    def __init__(self, output_text: str) -> None:
        self.output_text = output_text
        self.last_request = None

    def create(self, **kwargs):
        self.last_request = kwargs
        return SimpleNamespace(output_text=self.output_text)


class FakeOpenAI:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.responses = FakeResponses("print('hello')")


def test_generate_returns_code(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(agent_module, "OpenAI", FakeOpenAI)

    agent = CodeAgent()

    assert agent.generate("Print hello") == "print('hello')"


def test_generate_passes_feedback(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(agent_module, "OpenAI", FakeOpenAI)

    agent = CodeAgent()
    agent.generate("Write a palindrome function", feedback="AssertionError")

    request = agent.client.responses.last_request
    assert "AssertionError" in request["input"]


def test_generate_rejects_missing_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ValueError, match="OPENAI_API_KEY is missing"):
        CodeAgent()


def test_generate_rejects_empty_response(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(agent_module, "OpenAI", FakeOpenAI)

    agent = CodeAgent()
    agent.client.responses.output_text = "   "

    with pytest.raises(RuntimeError, match="empty code"):
        agent.generate("Write some code")
