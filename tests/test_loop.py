import pytest

from codepilot.loop import CodeLoop
from codepilot.runner import TestResult


class FakeAgent:
    def __init__(self, outputs):
        self.outputs = iter(outputs)
        self.calls = []
        self.test_calls = []

    def generate(self, task, feedback=None):
        self.calls.append({"task": task, "feedback": feedback})
        return next(self.outputs)

    def generate_tests(self, task, code):
        self.test_calls.append({"task": task, "code": code})
        return "class TestGenerated(unittest.TestCase):\n    def test_example(self):\n        self.assertTrue(True)"


class FakeRunner:
    def __init__(self, results):
        self.results = iter(results)
        self.calls = []

    def run(self, code, test_code):
        self.calls.append({"code": code, "test_code": test_code})
        return next(self.results)


def passed_result():
    return TestResult(
        passed=True,
        return_code=0,
        stdout="",
        stderr="",
    )


def failed_result():
    return TestResult(
        passed=False,
        return_code=1,
        stdout="",
        stderr="AssertionError: expected 5",
    )


def test_loop_passes_on_first_attempt():
    agent = FakeAgent(["correct code"])
    runner = FakeRunner([passed_result()])
    loop = CodeLoop(agent=agent, runner=runner)

    result = loop.run("Write a function")

    assert result.passed
    assert result.attempts == 1
    assert result.code == "correct code"
    assert len(agent.test_calls) == 1


def test_loop_retries_after_failure():
    agent = FakeAgent(["bad code", "correct code"])
    runner = FakeRunner([failed_result(), passed_result()])
    loop = CodeLoop(agent=agent, runner=runner, max_attempts=3)

    result = loop.run("Write a function")

    assert result.passed
    assert result.attempts == 2
    assert result.code == "correct code"
    assert "AssertionError" in agent.calls[1]["feedback"]

    # Tests are generated once and reused during repair.
    assert len(agent.test_calls) == 1
    assert runner.calls[0]["test_code"] == runner.calls[1]["test_code"]


def test_loop_stops_at_max_attempts():
    agent = FakeAgent(["bad code", "still bad"])
    runner = FakeRunner([failed_result(), failed_result()])
    loop = CodeLoop(agent=agent, runner=runner, max_attempts=2)

    result = loop.run("Write a function")

    assert not result.passed
    assert result.attempts == 2
    assert result.code == "still bad"
    assert len(agent.calls) == 2
    assert len(runner.calls) == 2


def test_loop_rejects_invalid_max_attempts():
    with pytest.raises(ValueError, match="max_attempts"):
        CodeLoop(
            agent=FakeAgent([]),
            runner=FakeRunner([]),
            max_attempts=0,
        )
