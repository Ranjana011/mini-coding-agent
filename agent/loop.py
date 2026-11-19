"""The heart of the project: the agent loop.

    user task -> [ LLM thinks -> calls tools -> sees results ] x N -> final answer

The loop keeps going while the model asks for tools, and stops when it
answers in plain text (or when it hits the step limit).
"""
import json
from typing import Callable

from .prompts import SYSTEM_PROMPT
from .tools import TOOL_SCHEMAS, Toolbox


class Agent:
    def __init__(self, llm, toolbox: Toolbox, max_steps: int = 25,
                 on_event: Callable[[str, dict], None] | None = None):
        self.llm = llm
        self.toolbox = toolbox
        self.max_steps = max_steps
        self.on_event = on_event or (lambda kind, data: None)
        self.messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

    def ask(self, task: str) -> str:
        self.messages.append({"role": "user", "content": task})

        for step in range(1, self.max_steps + 1):
            reply = self.llm.chat(self.messages, TOOL_SCHEMAS)
            self.messages.append(reply.to_message())

            if not reply.tool_calls:  # no tools requested -> model is done
                return reply.content or ""

            if reply.content:
                self.on_event("thought", {"text": reply.content})

            for call in reply.tool_calls:
                try:
                    args = json.loads(call.arguments or "{}")
                except json.JSONDecodeError:
                    args, result = None, "Error: arguments were not valid JSON."
                if args is not None:
                    self.on_event("tool_call", {"step": step, "name": call.name, "args": args})
                    result = self.toolbox.run(call.name, args)
                self.on_event("tool_result", {"name": call.name, "result": result})
                # The tool result goes back into history so the model can see it.
                self.messages.append({"role": "tool", "tool_call_id": call.id, "content": result})

        return f"Stopped after {self.max_steps} steps without finishing. Try a smaller task."

    def reset(self) -> None:
        self.messages = self.messages[:1]
