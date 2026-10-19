import re
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax

from codepilot.agent import CodeAgent
from codepilot.workflow import CodeWorkflow

app = typer.Typer(
    name="CodePilot",
    help="Generate, test, and repair Python code.",
    no_args_is_help=True,
)

console = Console()


def save_code(task: str, code: str) -> Path:
    """Save the generated implementation."""
    output_dir = Path("generated")
    output_dir.mkdir(parents=True, exist_ok=True)

    slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", task.lower()).strip("_")
    slug = slug[:40] or "solution"

    code_path = output_dir / f"{slug}.py"
    code_path.write_text(code.rstrip() + "\n", encoding="utf-8")
    return code_path


@contextmanager
def show_progress_step(label: str) -> Generator[None]:
    """Show one active step, then keep its completion visible."""
    with console.status(f"[cyan]{label}...", spinner="dots"):
        yield
    console.print(f"[bold green]✓ {label}[/bold green]")


def run_coding_task(
    agent: CodeAgent,
    task: str,
    max_attempts: int,
) -> None:
    """Generate, test, and display one coding task."""
    workflow = CodeWorkflow(
        agent=agent,
        max_attempts=max_attempts,
        show_progress=show_progress_step,
    )
    result = workflow.run(task=task)

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

    code_path = save_code(task, result.code)

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


def handle_message(
    agent: CodeAgent,
    message: str,
    max_attempts: int,
) -> None:
    """Route a message to a direct answer or the coding workflow."""
    with show_progress_step("Understanding your request"):
        decision = agent.route_message(message)

    if decision["intent"] == "chat":
        console.print(
            Panel(
                Markdown(decision["response"]),
                title="[bold cyan]CodePilot[/bold cyan]",
                border_style="cyan",
            )
        )
        return

    run_coding_task(agent, decision["response"], max_attempts)


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
    """Start an interactive conversational coding session."""
    console.print(
        Panel(
            "Ask questions or give me a coding task.\n"
            "Coding tasks are generated, tested, and repaired automatically.\n"
            "Type 'exit' or 'quit' to stop.",
            title="[bold cyan]CodePilot[/bold cyan]",
        )
    )

    agent = None

    while True:
        try:
            message = console.input("\n[bold cyan]you > [/bold cyan]").strip()
        except EOFError, KeyboardInterrupt:
            console.print("\n[yellow]Session ended.[/yellow]")
            break

        if not message:
            continue

        if message.lower() in {"exit", "quit"}:
            console.print("[yellow]Goodbye.[/yellow]")
            break

        try:
            if agent is None:
                agent = CodeAgent()

            handle_message(agent, message, max_attempts)

        except Exception as exc:  # noqa: BLE001
            console.print(f"[bold red]Error:[/bold red] {exc}")


if __name__ == "__main__":
    app()
