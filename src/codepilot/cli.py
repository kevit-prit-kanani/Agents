import re
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from codepilot.agent import CodeAgent
from codepilot.loop import CodeLoop

app = typer.Typer(
    name="CodePilot",
    help="Generate, test, and repair Python code.",
    no_args_is_help=True,
)

console = Console()


def save_result(task: str, code: str, test_code: str) -> tuple[Path, Path]:
    """Save the implementation and a runnable combined test script."""
    output_dir = Path("generated")
    output_dir.mkdir(parents=True, exist_ok=True)

    slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", task.lower()).strip("_")
    slug = slug[:40] or "solution"

    code_path = output_dir / f"{slug}.py"
    test_path = output_dir / f"{slug}_test_run.py"

    code_path.write_text(code.rstrip() + "\n", encoding="utf-8")

    combined = (
        code.rstrip()
        + "\n\nimport unittest\n\n"
        + test_code.strip()
        + "\n\nif __name__ == '__main__':\n"
        + "    unittest.main(verbosity=2)\n"
    )
    test_path.write_text(combined, encoding="utf-8")

    return code_path, test_path


@app.command()
def generate(
    task: str = typer.Argument(..., help="Describe the Python program."),
) -> None:
    """Generate code without testing it."""
    try:
        agent = CodeAgent()
        with console.status("[cyan]Generating code...", spinner="dots"):
            code = agent.generate(task=task)

        console.print(
            Panel(
                Syntax(code, "python", theme="monokai", line_numbers=True),
                title="Generated Python Code",
                border_style="green",
            )
        )
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc


@app.command()
def chat(
    max_attempts: int = typer.Option(
        3,
        "--max-attempts",
        min=1,
        help="Maximum implementation attempts.",
    ),
) -> None:
    """Start an interactive generate-test-repair session."""
    console.print(
        Panel(
            "Describe a Python task. CodePilot generates the code and tests it.\n"
            "Type 'exit' or 'quit' to stop.",
            title="[bold cyan]CodePilot[/bold cyan]",
        )
    )

    while True:
        try:
            task = console.input("\n[bold cyan]codepilot > [/bold cyan]").strip()
        except EOFError, KeyboardInterrupt:
            console.print("\n[yellow]Session ended.[/yellow]")
            break

        if not task:
            continue

        if task.lower() in {"exit", "quit"}:
            console.print("[yellow]Goodbye.[/yellow]")
            break

        try:
            agent = CodeAgent()
            loop = CodeLoop(agent=agent, max_attempts=max_attempts)

            with console.status(
                "[cyan]Generating code and tests, then running tests...",
                spinner="dots",
            ):
                result = loop.run(task=task)

            console.print(
                Panel(
                    Syntax(
                        result.code,
                        "python",
                        theme="monokai",
                        line_numbers=True,
                    ),
                    title="Final Python Implementation",
                    border_style="green" if result.passed else "red",
                )
            )

            code_path, test_path = save_result(
                task,
                result.code,
                result.test_code,
            )

            if result.passed:
                console.print(
                    f"[bold green]Tests passed[/bold green] "
                    f"on attempt {result.attempts}/{max_attempts}."
                )
            else:
                console.print(
                    f"[bold red]Tests did not pass[/bold red] "
                    f"after {result.attempts} attempt(s)."
                )
                console.print(
                    Panel(
                        result.test_result.feedback,
                        title="Final Test Feedback",
                        border_style="red",
                    )
                )

            console.print(f"Implementation saved to: [cyan]{code_path}[/cyan]")
            console.print(f"Combined test script saved to: [cyan]{test_path}[/cyan]")

        except Exception as exc:
            console.print(f"[bold red]Task failed:[/bold red] {exc}")


if __name__ == "__main__":
    app()
