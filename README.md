# Mini Coding Agent 🤖

A minimal AI coding agent built from scratch in Python, inspired by Claude Code,
GitHub Copilot and Cursor Agent. You give it a task in plain English; it reads
files, writes and edits code, runs commands, looks at the results, and keeps
going until the task is done.

> Project 1: *Build Your Own AI Coding Agent*

## Features

- **Agent loop**: think → call tools → observe results → repeat
- **6 tools**: `list_files`, `read_file`, `write_file`, `edit_file`, `search`, `run_shell`
- **Safety**: sandboxed workspace, human approval for shell commands, timeouts, step limit
- **Any provider**: Groq / Gemini (free tiers), Ollama (local), or OpenAI, chosen in `.env`
- **Tested**: unit tests for tools and the loop using a fake LLM (no API key needed)

## Architecture

See [docs/architecture.md](docs/architecture.md) for the diagram and design decisions.

```
mini-coding-agent/
├── agent/
│   ├── main.py      # CLI entry point
│   ├── loop.py      # the agent loop
│   ├── llm.py       # LLM API wrapper
│   ├── tools.py     # tools + JSON schemas + sandbox
│   ├── prompts.py   # system prompt
│   └── config.py    # settings from .env
├── tests/           # pytest tests
├── docs/            # architecture, report, screenshots
├── .env.example     # config template (copy to .env)
└── requirements.txt
```

## Setup

```bash
git clone https://github.com/<your-username>/mini-coding-agent.git
cd mini-coding-agent
python -m venv .venv
# Windows: .venv\Scripts\activate      macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # Windows: copy .env.example .env
```

Edit `.env` and add an API key (Groq: https://console.groq.com/keys,
Gemini: https://aistudio.google.com/apikey).

## Usage

```bash
python -m agent.main
```

```
you › create a python file calculator.py with add, subtract, multiply, divide functions and a test file, then run the tests
🔧 [1] write_file(path='calculator.py', ...)
🔧 [2] write_file(path='test_calculator.py', ...)
Run `python -m pytest -q`? [y/N] y
🔧 [3] run_shell(command='python -m pytest -q')
   ↳ exit code: 0 ...
agent › Created calculator.py and test_calculator.py; all 4 tests pass.
```

Options: `--workspace <folder>` to work in another folder, `--yes` to auto-approve shell commands.

## Run tests

```bash
python -m pytest -q
```

## How it works (short version)

1. Your task is added to the conversation `messages`.
2. The LLM receives the messages plus the tool schemas and replies with either
   text (done) or one or more **tool calls**.
3. The agent executes each tool and appends the result as a `tool` message.
4. Steps 2–3 repeat until the LLM replies without tool calls or the step limit is hit.

## Roadmap

- [x] Basic agent loop with tools
- [x] Sandbox + shell approval
- [ ] Context compression for long sessions
- [ ] Git tools (diff, commit)
- [ ] Multi-agent SDLC pipeline (Project 2)
