from contextlib import contextmanager

import pytest

from codepilot.runner import TestResult
from codepilot.workflow import CodeWorkflow


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


def test_workflow_passes_on_first_attempt():
    agent = FakeAgent(["correct code"])
    runner = FakeRunner([passed_result()])
    workflow = CodeWorkflow(agent=agent, runner=runner)

    result = workflow.run("Write a function")

    assert result.passed
    assert result.attempts == 1
    assert result.code == "correct code"
    assert len(agent.test_calls) == 1


def test_workflow_reports_each_completed_step():
    completed_steps = []

    @contextmanager
    def record_step(label):
        yield
        completed_steps.append(label)

    workflow = CodeWorkflow(
        agent=FakeAgent(["correct code"]),
        runner=FakeRunner([passed_result()]),
        show_progress=record_step,
    )

    workflow.run("Write a function")

    assert completed_steps == [
        "Writing the first implementation",
        "Preparing checks",
        "Running checks (attempt 1/3)",
    ]


def test_workflow_retries_after_failure():
    agent = FakeAgent(["bad code", "correct code"])
    runner = FakeRunner([failed_result(), passed_result()])
    workflow = CodeWorkflow(agent=agent, runner=runner, max_attempts=3)

    result = workflow.run("Write a function")

    assert result.passed
    assert result.attempts == 2
    assert result.code == "correct code"
    assert "AssertionError" in agent.calls[1]["feedback"]

    # Tests are generated once and reused during repair.
    assert len(agent.test_calls) == 1
    assert runner.calls[0]["test_code"] == runner.calls[1]["test_code"]


def test_workflow_stops_at_max_attempts():
    agent = FakeAgent(["bad code", "still bad"])
    runner = FakeRunner([failed_result(), failed_result()])
    workflow = CodeWorkflow(agent=agent, runner=runner, max_attempts=2)

    result = workflow.run("Write a function")

    assert not result.passed
    assert result.attempts == 2
    assert result.code == "still bad"
    assert len(agent.calls) == 2
    assert len(runner.calls) == 2


def test_workflow_rejects_invalid_max_attempts():
    with pytest.raises(ValueError, match="max_attempts"):
        CodeWorkflow(
            agent=FakeAgent([]),
            runner=FakeRunner([]),
            max_attempts=0,
        )
