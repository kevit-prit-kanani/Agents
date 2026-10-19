import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TestResult:
    """Structured result returned by the test runner."""

    __test__ = False

    passed: bool
    return_code: int | None
    stdout: str
    stderr: str
    time_out: bool = False

    @property
    def feedback(self) -> str:
        """Format test output for display or LLM repair feedback."""
        if self.passed:
            return "All tests passed!"

        if self.time_out:
            return "Execution timed out"

        return (
            f"Exit code: {self.return_code}\n"
            f"STDOUT:\n{self.stdout}\n"
            f"STDERR:\n{self.stderr}"
        )


class TestRunner:
    """Execute candidate code with a predefined test suite."""

    __test__ = False

    def __init__(self, timeout: int = 5) -> None:
        if timeout <= 0:
            raise ValueError("timeout must be greater than zero")

        self.timeout = timeout

    def run(self, code: str, test_code: str) -> TestResult:
        """
        Run candidate code and trusted tests in a child Python process.

        test_code must be supplied by the application, not by the LLM.
        """

        with tempfile.TemporaryDirectory(prefix="codepilot-") as tmp:
            script_path = Path(tmp) / "candidate_test.py"
            script_path.write_text(
                code
                + "\n\n"
                + "import unittest\n"
                + test_code
                + "\n\n"
                + 'if __name__ == "__main__":\n'
                + "\tunittest.main(verbosity=2)\n",
                encoding="utf-8",
            )
            try:
                completed = subprocess.run(
                    [sys.executable, "-I", str(script_path)],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    check=False,
                    cwd=tmp,
                )
                return TestResult(
                    passed=completed.returncode == 0,
                    return_code=completed.returncode,
                    stdout=completed.stdout,
                    stderr=completed.stderr,
                )
            except subprocess.TimeoutExpired as exc:
                stdout = exc.stdout or ""
                stderr = exc.stderr or ""

                if isinstance(stdout, bytes):
                    stdout = stdout.decode("utf-8", errors="replace")

                if isinstance(stderr, bytes):
                    stderr = stderr.decode("utf-8", errors="replace")

                return TestResult(
                    passed=False,
                    return_code=None,
                    stdout=stdout,
                    stderr=stderr,
                    time_out=True,
                )
