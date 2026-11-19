"""Thin wrapper around the LLM API.

The rest of the agent never touches the provider SDK directly: it only sees
`LLMReply`. That makes it easy to swap providers or plug in a fake LLM for tests.
"""
from dataclasses import dataclass, field


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: str  # raw JSON string, exactly as the model produced it


@dataclass
class LLMReply:
    content: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)

    def to_message(self) -> dict:
        """Convert to the assistant message format stored in conversation history."""
        msg = {"role": "assistant", "content": self.content or ""}
        if self.tool_calls:
            msg["tool_calls"] = [
                {"id": c.id, "type": "function",
                 "function": {"name": c.name, "arguments": c.arguments}}
                for c in self.tool_calls
            ]
        return msg


class LLMClient:
    def __init__(self, api_key: str, model: str, base_url: str | None = None):
        from openai import OpenAI  # imported here so tests don't need the package
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def chat(self, messages: list[dict], tools: list[dict]) -> LLMReply:
        resp = self.client.chat.completions.create(
            model=self.model, messages=messages, tools=tools, temperature=0.2,
        )
        m = resp.choices[0].message
        calls = [ToolCall(c.id, c.function.name, c.function.arguments or "{}")
                 for c in (m.tool_calls or [])]
        return LLMReply(content=m.content, tool_calls=calls)
