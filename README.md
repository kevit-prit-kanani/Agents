# CodePilot

CodePilot is a command-line Python assistant that can answer questions and
generate, test, and repair small Python programs.

## Project structure

- `src/codepilot/agent.py` talks to the language model.
- `src/codepilot/workflow.py` coordinates code generation, testing, and retries.
- `src/codepilot/runner.py` runs generated code and tests in a temporary folder.
- `src/codepilot/cli.py` handles terminal input, output, and saving solutions.
- `tests/` contains the project's own automated checks.

Generated test code is used only during the temporary test run. CodePilot saves
the generated implementation under `generated/`; it does not save generated
test scripts.

During interactive work, CodePilot shows each active stage and marks completed
stages before moving on to the next one.

The chat prompt suggests matching slash commands as you type. Use `/help` to
list commands, and `/exit` or `/quit` to end the chat.

## Run

Install the package, save your OpenAI API key, and start the interactive
session:

```console
pipx install codepilot-00
codepilot setup
codepilot chat
```

The PyPI distribution is named `codepilot-00`; the installed terminal command
is `codepilot`.

If you prefer not to use `pipx`, install the distribution in a virtual
environment and ensure its scripts directory is on your `PATH`:

```console
python -m pip install codepilot-00
```

Generate code directly without the interactive session:

```console
uv run codepilot generate "Write a function that checks whether text is a palindrome"
```

See the [installation and publishing guide](https://github.com/kevit-prit-kanani/Agents/blob/master/SETUP.md)
for detailed instructions.