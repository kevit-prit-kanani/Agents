import re
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

import typer
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax

from codepilot.agent import CodeAgent
from codepilot.settings import save_api_key
from codepilot.workflow import CodeWorkflow

app = typer.Typer(
    name="CodePilot",
    help="Generate, test, and repair Python code.",
    no_args_is_help=True,
)

console = Console()

SLASH_COMMANDS = {
    "/help": "Show available commands",
    "/exit": "Exit CodePilot",
    "/quit": "Exit CodePilot",
}


class SlashCommandCompleter(Completer):
    """Suggest available slash commands while the user types."""

    def get_completions(
        self,
        document: Document,
        complete_event: CompleteEvent,
    ) -> Generator[Completion]:
        prefix = document.text_before_cursor
        if not prefix.startswith("/") or any(char.isspace() for char in prefix):
            return

        for command, description in SLASH_COMMANDS.items():
            if command.startswith(prefix.lower()):
                yield Completion(
                    command,
                    start_position=-len(prefix),
                    display_meta=description,
                )


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


def handle_slash_command(message: str) -> bool | None:
    """Run a slash command; return whether the chat should exit."""
    command = message.strip().lower()

    if command in {"/exit", "/quit"}:
        return True
    if command == "/help":
        console.print(
            Panel(
                "\n".join(
                    f"[cyan]{name}[/cyan] — {description}"
                    for name, description in SLASH_COMMANDS.items()
                ),
                title="Available commands",
            )
        )
        return False
    if command.startswith("/"):
        console.print(
            f"[yellow]Unknown command:[/yellow] {command}. "
            "Type /help to see available commands."
        )
        return False
    return None


@app.command()
def setup() -> None:
    """Save or replace the OpenAI API key for this user."""
    api_key = typer.prompt(
        "OpenAI API key",
        hide_input=True,
        confirmation_prompt=True,
    )
    try:
        config_file = save_api_key(api_key)
    except (OSError, ValueError) as exc:
        console.print(f"[bold red]Could not save API key:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(
        "[bold green]API key saved.[/bold green] "
        f"Configuration file: [cyan]{config_file}[/cyan]"
    )


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
            "Type /help for commands. Use /exit or /quit to stop.",
            title="[bold cyan]CodePilot[/bold cyan]",
        )
    )

    agent = None
    prompt_session = PromptSession(
        completer=SlashCommandCompleter(),
        complete_while_typing=True,
    )

    while True:
        try:
            message = prompt_session.prompt("you > ").strip()
        except KeyboardInterrupt:
            console.print(
                "\n[yellow]Input cancelled. Use /exit or /quit to end the chat.[/yellow]"
            )
            continue
        except EOFError:
            console.print("\n[yellow]Input stream closed.[/yellow]")
            break

        if not message:
            continue

        should_exit = handle_slash_command(message)
        if should_exit is True:
            console.print("[yellow]Goodbye.[/yellow]")
            break
        if should_exit is False:
            continue

        try:
            if agent is None:
                agent = CodeAgent()

            handle_message(agent, message, max_attempts)

        except Exception as exc:  # noqa: BLE001
            console.print(f"[bold red]Error:[/bold red] {exc}")


if __name__ == "__main__":
    app()
