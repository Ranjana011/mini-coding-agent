# Architecture

## Overview

```
┌──────────────┐   task    ┌──────────────────────── Agent loop (loop.py) ────────────────────────┐
│  CLI (main)  │ ────────▶ │                                                                      │
│  you › ...   │           │   messages ──▶ LLM (llm.py) ──▶ reply                                │
└──────────────┘           │                                   │                                  │
       ▲                   │              tool_calls? ── no ──▶ return final answer ──────────────┼──▶ printed
       │ approve shell?    │                   │ yes                                              │
       └───────────────────┼── Toolbox (tools.py): list / read / write / edit / search / shell    │
                           │                   │                                                  │
                           │   tool results appended to messages, loop again (max N steps)       │
                           └──────────────────────────────────────────────────────────────────────┘
                                               │
                                     workspace/ (sandboxed folder)
```

## Modules

| File | Responsibility |
|------|----------------|
| `agent/main.py` | Interactive CLI, prints each step, asks approval for shell commands |
| `agent/loop.py` | The agent loop: call LLM → run requested tools → feed results back → repeat |
| `agent/llm.py` | Wraps the provider API; returns a provider-neutral `LLMReply` |
| `agent/tools.py` | Tool implementations + JSON schemas the model sees; sandboxing |
| `agent/prompts.py` | System prompt that teaches the model how to work |
| `agent/config.py` | Reads `.env`; provider presets (Groq, Gemini, Ollama, OpenAI) |
| `tests/` | Unit tests for tools and the loop (fake LLM, no API key needed) |

## Design decisions

1. **OpenAI-compatible API format.** Groq, Gemini, Ollama and OpenAI all accept it,
   so switching provider is a one-line change in `.env`.
2. **Provider-neutral `LLMReply`.** The loop never sees SDK objects. This made it
   possible to test the loop with a scripted `FakeLLM`.
3. **Tool errors are returned, not raised.** If the model passes a wrong path, it
   gets `Error: ...` as the tool result and can correct itself, instead of crashing.
4. **`edit_file` uses exact, unique string replacement** (like Claude Code), which is
   safer than rewriting whole files and forces the model to read before editing.
5. **Safety:** file access is confined to the workspace folder (path traversal like
   `../` is blocked), shell commands need human approval, commands time out, outputs
   are truncated, and the loop has a max step limit.

## Limitations / future work

- Conversation history grows without limit (could summarise old turns).
- `search` is plain substring search, not regex or semantic search.
- No git integration, no undo for file edits.
- Single agent; Project 2 will split work across multiple specialised agents.
