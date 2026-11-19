"""Tests the agent loop with a scripted fake LLM, so no API key is needed."""
import json

from agent.llm import LLMReply, ToolCall
from agent.loop import Agent
from agent.tools import Toolbox


class FakeLLM:
    def __init__(self, replies):
        self.replies = list(replies)
        self.seen = []

    def chat(self, messages, tools):
        self.seen.append(list(messages))
        return self.replies.pop(0)


def call(i, name, **args):
    return ToolCall(id=f"c{i}", name=name, arguments=json.dumps(args))


def test_agent_uses_tools_then_answers(tmp_path):
    llm = FakeLLM([
        LLMReply("I'll create the file.", [call(1, "write_file", path="add.py",
                                                    content="print(2 + 3)\n")]),
        LLMReply(None, [call(2, "run_shell", command="python3 add.py")]),
        LLMReply("Done: add.py prints 5."),
    ])
    agent = Agent(llm, Toolbox(tmp_path, confirm=lambda c: True))
    assert agent.ask("make add.py") == "Done: add.py prints 5."
    assert (tmp_path / "add.py").exists()
    # the shell output (5) was fed back to the model before its final answer
    last_tool_msg = llm.seen[-1][-1]
    assert last_tool_msg["role"] == "tool" and "5" in last_tool_msg["content"]


def test_step_limit(tmp_path):
    looping = [LLMReply(None, [call(i, "list_files")]) for i in range(5)]
    agent = Agent(FakeLLM(looping), Toolbox(tmp_path), max_steps=3)
    assert "Stopped after 3 steps" in agent.ask("loop forever")


def test_bad_json_arguments_reported(tmp_path):
    llm = FakeLLM([
        LLMReply(None, [ToolCall("c1", "read_file", "{not json")]),
        LLMReply("ok"),
    ])
    agent = Agent(llm, Toolbox(tmp_path))
    agent.ask("x")
    assert "not valid JSON" in llm.seen[-1][-1]["content"]
