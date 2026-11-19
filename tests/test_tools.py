from agent.tools import Toolbox


def test_write_read_edit(tmp_path):
    tb = Toolbox(tmp_path)
    assert "Wrote" in tb.run("write_file", {"path": "a/hello.py", "content": "print('hi')\n"})
    assert "print('hi')" in tb.run("read_file", {"path": "a/hello.py"})
    assert "Edited" in tb.run("edit_file", {"path": "a/hello.py", "old": "hi", "new": "bye"})
    assert (tmp_path / "a/hello.py").read_text() == "print('bye')\n"


def test_sandbox_blocks_escape(tmp_path):
    tb = Toolbox(tmp_path / "ws")
    assert "outside the workspace" in tb.run("read_file", {"path": "../secret.txt"})


def test_edit_requires_unique_match(tmp_path):
    tb = Toolbox(tmp_path)
    tb.write_file("x.txt", "a a")
    assert "appears 2 times" in tb.run("edit_file", {"path": "x.txt", "old": "a", "new": "b"})


def test_shell_needs_approval(tmp_path):
    denied = Toolbox(tmp_path, confirm=lambda c: False)
    assert "declined" in denied.run("run_shell", {"command": "echo hi"})
    allowed = Toolbox(tmp_path, confirm=lambda c: True)
    assert "hi" in allowed.run("run_shell", {"command": "echo hi"})


def test_unknown_tool_and_bad_args(tmp_path):
    tb = Toolbox(tmp_path)
    assert "unknown tool" in tb.run("delete_everything", {})
    assert "bad arguments" in tb.run("read_file", {})
