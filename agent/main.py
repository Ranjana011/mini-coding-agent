"""Command-line interface: an interactive chat with the agent.

Usage:
    python -m agent.main                      # works in ./workspace
    python -m agent.main --workspace my_proj  # works in another folder
    python -m agent.main --yes                # auto-approve shell commands (careful!)
"""
import argparse

from .config import load_config
from .llm import LLMClient
from .loop import Agent
from .tools import Toolbox

CYAN, YELLOW, GREEN, DIM, RESET = "\033[36m", "\033[33m", "\033[32m", "\033[2m", "\033[0m"


def show(kind: str, data: dict) -> None:
    if kind == "thought":
        print(f"{DIM}💭 {data['text']}{RESET}")
    elif kind == "tool_call":
        args = ", ".join(f"{k}={str(v)[:60]!r}" for k, v in data["args"].items())
        print(f"{YELLOW}🔧 [{data['step']}] {data['name']}({args}){RESET}")
    elif kind == "tool_result":
        preview = data["result"].strip().splitlines()[:3]
        print(f"{DIM}   ↳ " + "\n     ".join(preview) + RESET)


def main() -> None:
    ap = argparse.ArgumentParser(description="Mini Coding Agent")
    ap.add_argument("--workspace", default="workspace", help="Folder the agent may work in")
    ap.add_argument("--yes", action="store_true", help="Auto-approve shell commands")
    args = ap.parse_args()

    cfg = load_config()

    def confirm(cmd: str) -> bool:
        if args.yes:
            return True
        return input(f"{CYAN}Run `{cmd}`? [y/N] {RESET}").strip().lower() == "y"

    agent = Agent(
        llm=LLMClient(cfg.api_key, cfg.model, cfg.base_url),
        toolbox=Toolbox(args.workspace, confirm=confirm),
        max_steps=cfg.max_steps,
        on_event=show,
    )
    print(f"{GREEN}Mini Coding Agent{RESET} · {cfg.provider}/{cfg.model} · workspace: {args.workspace}")
    print("Type a task. Commands: /reset (clear memory), /exit\n")

    while True:
        try:
            task = input(f"{CYAN}you › {RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not task:
            continue
        if task == "/exit":
            break
        if task == "/reset":
            agent.reset()
            print("Memory cleared.")
            continue
        try:
            print(f"\n{GREEN}agent ›{RESET} {agent.ask(task)}\n")
        except KeyboardInterrupt:
            print("\n(interrupted)")
        except Exception as e:
            print(f"\nLLM error: {e}\n")


if __name__ == "__main__":
    main()
