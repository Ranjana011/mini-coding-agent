# Mini Coding Agent 🤖

A minimal AI coding agent built from scratch in Python. Describe a task in plain
English and the agent reads files, writes and edits code, runs commands, checks
the results, and keeps going until the job is done — all from your terminal.

Inspired by tools like Claude Code, GitHub Copilot and Cursor Agent, but small
enough to read in one sitting.

```
you › create calculator.py with add, subtract, multiply, divide and a test file, then run the tests
🔧 [1] write_file(path='calculator.py', ...)
🔧 [2] write_file(path='test_calculator.py', ...)
Run `python -m pytest -q`? [y/N] y
🔧 [3] run_shell(command='python -m pytest -q')
   ↳ exit code: 0 ...
agent › Created calculator.py and test_calculator.py; all 4 tests pass.
```

## Features

- **Agent loop** — think → call tools → observe results → repeat, until the task is done
- **Six tools** — list, read, write, edit and search files, plus run shell commands
- **Safe by default** — sandboxed workspace, approval before every shell command, timeouts and a step limit
- **Works with any provider** — Groq or Gemini (free tiers), Ollama (fully local) or OpenAI
- **Self-correcting** — tool errors are fed back to the model so it can fix its own mistakes
- **Tested** — unit tests for the tools and the loop using a fake LLM, no API key needed

## Quick start

**Requirements:** Python 3.10+ and an API key from one of the supported providers
(or [Ollama](https://ollama.com) running locally).

```bash
git clone https://github.com/Ranjana011/mini-coding-agent.git
cd mini-coding-agent

python -m venv .venv
# Windows:      .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env      # Windows: copy .env.example .env
```

Open `.env` and add your key, then start the agent:

```bash
python -m agent.main
```

## Configuration

All settings live in `.env`:

| Variable | Description | Default |
|---|---|---|
| `LLM_PROVIDER` | `groq`, `gemini`, `ollama` or `openai` | `groq` |
| `LLM_API_KEY` | API key for the provider (not needed for Ollama) | — |
| `LLM_MODEL` | Override the provider's default model | see below |
| `MAX_STEPS` | Maximum tool-calling steps per task | `25` |

| Provider | Default model | Get a key |
|---|---|---|
| Groq | `openai/gpt-oss-120b` | [console.groq.com/keys](https://console.groq.com/keys) |
| Gemini | `gemini-2.5-flash` | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| Ollama | `qwen2.5-coder:7b` | runs locally, no key |
| OpenAI | `gpt-4o-mini` | [platform.openai.com](https://platform.openai.com/api-keys) |

> ⚠️ `.env` is git-ignored. Never commit your API key.

## Usage

```bash
python -m agent.main                        # work inside ./workspace
python -m agent.main --workspace my_project # work inside another folder
python -m agent.main --yes                  # auto-approve shell commands (use with care)
```

Inside the chat:

| Command | Action |
|---|---|
| *any text* | Give the agent a task |
| `/undo` | Put back the files the last task wrote or edited |
| `/reset` | Clear the conversation memory |
| `/exit` | Quit |

## Tools

| Tool | What it does |
|---|---|
| `list_files` | List files and folders in the workspace |
| `read_file` | Read a file, with line numbers |
| `write_file` | Create a file or overwrite it completely |
| `edit_file` | Replace one exact, unique snippet of text in a file |
| `search` | Find lines containing a pattern across files |
| `run_shell` | Run a shell command in the workspace (requires your approval) |

## How it works

1. Your task is added to the conversation history.
2. The LLM receives the history plus the tool definitions and replies with either
   a final answer or one or more **tool calls**.
3. The agent runs each tool and adds the result to the history.
4. Steps 2–3 repeat until the model answers without calling a tool, or the step
   limit is reached.

### Safety

- **Sandbox** — every file operation is confined to the workspace folder; paths like `../` are blocked.
- **Human approval** — each shell command is shown to you and only runs if you type `y`.
- **Timeouts** — shell commands are stopped after 60 seconds.
- **Output limits** — long tool output is truncated so it doesn't flood the model's context.
- **Step limit** — the loop stops after `MAX_STEPS` iterations.

See [docs/architecture.md](docs/architecture.md) for the full diagram and design decisions.

## Project structure

```
mini-coding-agent/
├── agent/
│   ├── main.py      # CLI entry point
│   ├── loop.py      # the agent loop
│   ├── llm.py       # LLM API wrapper
│   ├── tools.py     # tools, JSON schemas and sandbox
│   ├── prompts.py   # system prompt
│   └── config.py    # settings loaded from .env
├── tests/           # pytest tests (fake LLM, no API key needed)
├── docs/            # architecture and design notes
├── .env.example     # configuration template
└── requirements.txt
```

## Running tests

```bash
python -m pytest -q
```

## Roadmap

- [x] Agent loop with tool calling
- [x] Sandboxed workspace and shell approval
- [ ] Context compression for long sessions
- [ ] Git tools (diff, commit)
- [ ] Regex search
