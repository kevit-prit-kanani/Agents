
import os
import re

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def clean_code(text: str) -> str:
    """Remove optional Markdown fences from generated code."""
    text = text.strip()
    text = re.sub(
        r"\A```(?:python|py)?[ \t]*\r?\n?",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\r?\n?```[ \t]*\Z", "", text)
    return text.strip()


class CodeAgent:
    """Generate Python implementations and their tests."""

    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY is missing. Configure it in your .env file."
            )

        self.model = os.getenv("OPENAI_MODEL", "gpt-5.5")
        self.client = OpenAI(api_key=api_key)

    def _request(self, instructions: str, prompt: str) -> str:
        response = self.client.responses.create(
            model=self.model,
            instructions=instructions,
            input=prompt,
        )
        code = clean_code(response.output_text or "")
        if not code:
            raise RuntimeError("The model returned empty code.")
        return code

    def generate(
        self,
        task: str,
        feedback: str | None = None,
    ) -> str:
        """Generate or repair a Python implementation."""
        instructions = """
You are a Python code generation agent.

Requirements:
- Return Python implementation code only.
- Do not include Markdown fences or explanations.
- Prefer simple, readable, maintainable code.
- Do not include tests in the implementation.
- Correct the implementation using any provided test feedback.
- Do not claim that the code passed tests unless it was tested.
"""
        prompt = f"Programming task:\n{task}"

        if feedback:
            prompt += (
                "\n\nThe previous implementation failed its tests."
                "\nFix the implementation using this feedback."
                f"\n\nTest feedback:\n{feedback}"
            )

        return self._request(instructions, prompt)

    def generate_tests(self, task: str, code: str) -> str:
        """Generate unittest tests for the candidate implementation."""
        instructions = """
You are a Python test engineer.

Requirements:
- Return Python unittest test code only.
- Do not include Markdown fences or explanations.
- Do not repeat or redefine the candidate implementation.
- The candidate implementation will appear before your test code
  in the same Python file.
- Use unittest.TestCase and test methods beginning with test_.
- Test normal behavior, boundary cases, and relevant invalid inputs.
- Derive expected results from the user's task, not from assumptions
  that merely make the candidate implementation pass.
- Do not modify files, access the network, or run shell commands.
"""
        prompt = (
            f"User's programming task:\n{task}\n\n"
            f"Candidate implementation:\n{code}\n\n"
            "Write a unittest test suite for this implementation."
        )

        return self._request(instructions, prompt)
