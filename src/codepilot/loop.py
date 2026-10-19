
from dataclasses import dataclass

from codepilot.agent import CodeAgent
from codepilot.runner import TestResult, TestRunner


@dataclass
class LoopResult:
    """Outcome of a generate-test-repair run."""

    code: str
    test_code: str
    attempts: int
    test_result: TestResult

    @property
    def passed(self) -> bool:
        return self.test_result.passed


class CodeLoop:
    """Generate code and tests, execute them, and retry on failure."""

    def __init__(
        self,
        agent: CodeAgent | None = None,
        runner: TestRunner | None = None,
        max_attempts: int = 3,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")

        self.agent = agent if agent is not None else CodeAgent()
        self.runner = runner if runner is not None else TestRunner()
        self.max_attempts = max_attempts

    def run(self, task: str) -> LoopResult:
        """Generate implementation and tests, then retry on failures."""
        code = self.agent.generate(task=task)
        test_code = self.agent.generate_tests(task=task, code=code)

        for attempt in range(1, self.max_attempts + 1):
            result = self.runner.run(code=code, test_code=test_code)

            if result.passed:
                return LoopResult(
                    code=code,
                    test_code=test_code,
                    attempts=attempt,
                    test_result=result,
                )

            if attempt < self.max_attempts:
                code = self.agent.generate(
                    task=task,
                    feedback=result.feedback,
                )

        return LoopResult(
            code=code,
            test_code=test_code,
            attempts=self.max_attempts,
            test_result=result,
        )
