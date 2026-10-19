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

## Run

Set `OPENAI_API_KEY` in `.env`, then start the interactive session:

```console
uv run codepilot chat
```

Generate code directly without the interactive session:

```console
uv run codepilot generate "Write a function that checks whether text is a palindrome"
```