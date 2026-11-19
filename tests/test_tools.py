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


def test_undo_restores_files_from_before_the_task(tmp_path):
    tb = Toolbox(tmp_path)
    (tmp_path / "old.py").write_text("x = 1\n")

    tb.start_task()
    tb.run("edit_file", {"path": "old.py", "old": "1", "new": "2"})
    tb.run("edit_file", {"path": "old.py", "old": "2", "new": "3"})  # edited twice
    tb.run("write_file", {"path": "new.py", "content": "print('new')\n"})

    assert tb.undo() == ["new.py", "old.py"]
    assert (tmp_path / "old.py").read_text() == "x = 1\n"  # back to before the task
    assert not (tmp_path / "new.py").exists()               # created file removed
    assert tb.undo() == []                                  # nothing left to undo
    assert "unknown tool" in tb.run("undo", {})             # the model can't call it
