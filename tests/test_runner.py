from codepilot.runner import TestRunner


def test_runner_passes_correct_implementation():
    code = """
def is_palindrome(text):
    cleaned = ''.join(
        char.lower() for char in text if char != ' '
    )
    return cleaned == cleaned[::-1]
"""

    tests = """
class TestPalindrome(unittest.TestCase):
    def test_palindrome(self):
        self.assertTrue(is_palindrome("level"))

    def test_case_and_spaces(self):
        self.assertTrue(is_palindrome("Race Car"))

    def test_non_palindrome(self):
        self.assertFalse(is_palindrome("python"))

    def test_empty_string(self):
        self.assertTrue(is_palindrome(""))

    def test_spaces_in_non_palindrome(self):
        self.assertFalse(is_palindrome("hello world"))
"""

    result = TestRunner().run(code, tests)

    assert result.passed, result.feedback
    assert "Ran 5 tests" in result.stderr


def test_runner_captures_assertion_failure():
    code = """
def is_palindrome(text):
    return True
"""

    tests = """
class TestPalindrome(unittest.TestCase):
    def test_non_palindrome(self):
        self.assertFalse(is_palindrome("python"))
"""

    result = TestRunner().run(code, tests)

    assert not result.passed
    assert "AssertionError" in result.stderr


def test_runner_captures_syntax_error():
    code = "def broken(:\n    pass"

    result = TestRunner().run(code, "class TestExample(unittest.TestCase):\n    pass")

    assert not result.passed
    assert "SyntaxError" in result.stderr


def test_runner_times_out():
    code = """
while True:
    pass
"""

    result = TestRunner(timeout=1).run(
        code,
        "class TestExample(unittest.TestCase):\n    pass",
    )

    assert not result.passed
    assert result.timed_out
