
from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass
from typing import Callable

from codepilot.agent import CodeAgent
from codepilot.runner import TestResult, TestRunner


@dataclass
class WorkflowResult:
    """Outcome of a generate-test-repair run."""

    code: str
    test_code: str
    attempts: int
    test_result: TestResult

    @property
    def passed(self) -> bool:
        return self.test_result.passed


class CodeWorkflow:
    """Generate code and tests, execute them, and retry on failure."""

    def __init__(
        self,
        agent: CodeAgent | None = None,
        runner: TestRunner | None = None,
        max_attempts: int = 3,
        show_progress: Callable[[str], AbstractContextManager[None]] | None = None,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")

        self.agent = agent if agent is not None else CodeAgent()
        self.runner = runner if runner is not None else TestRunner()
        self.max_attempts = max_attempts
        self.show_progress = show_progress

    def run(self, task: str) -> WorkflowResult:
        """Generate implementation and tests, then retry on failures."""
        with self._progress_step("Writing the first implementation"):
            code = self.agent.generate(task=task)

        with self._progress_step("Preparing checks"):
            test_code = self.agent.generate_tests(task=task, code=code)

        for attempt in range(1, self.max_attempts + 1):
            with self._progress_step(
                f"Running checks (attempt {attempt}/{self.max_attempts})"
            ):
                result = self.runner.run(code=code, test_code=test_code)

            if result.passed:
                return WorkflowResult(
                    code=code,
                    test_code=test_code,
                    attempts=attempt,
                    test_result=result,
                )

            if attempt < self.max_attempts:
                with self._progress_step(
                    f"Improving the implementation (attempt "
                    f"{attempt + 1}/{self.max_attempts})"
                ):
                    code = self.agent.generate(
                        task=task,
                        feedback=result.feedback,
                    )

        return WorkflowResult(
            code=code,
            test_code=test_code,
            attempts=self.max_attempts,
            test_result=result,
        )

    def _progress_step(self, label: str) -> AbstractContextManager[None]:
        if self.show_progress is None:
            return nullcontext()
        return self.show_progress(label)
