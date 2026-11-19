"""The agent's tools: what it can actually *do* in the world.

Every file operation is confined to a workspace folder (the "sandbox"), and
shell commands need the user's approval before they run.
"""
import subprocess
from pathlib import Path
from typing import Callable

MAX_OUTPUT = 8000  # characters; keeps huge outputs from flooding the model's context


class ToolError(Exception):
    """An expected failure we report back to the model so it can recover."""


def _truncate(text: str) -> str:
    if len(text) <= MAX_OUTPUT:
        return text
    return text[:MAX_OUTPUT] + f"\n... [truncated {len(text) - MAX_OUTPUT} chars]"


class Toolbox:
    def __init__(self, root: str | Path, confirm: Callable[[str], bool] | None = None,
                 shell_timeout: int = 60):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.confirm = confirm or (lambda _cmd: False)  # deny shell by default
        self.shell_timeout = shell_timeout
        # Backups for /undo: file path -> its bytes before the current task
        # changed it (None = the file did not exist yet).
        self._backups: dict[Path, bytes | None] = {}

    # ---------- undo ----------
    def start_task(self) -> None:
        """Forget old backups; called at the start of every new task."""
        self._backups = {}

    def _backup(self, p: Path) -> None:
        # Only the first change in a task is saved, so undo goes back to the
        # version from *before* the task, not just before the last edit.
        if p not in self._backups:
            self._backups[p] = p.read_bytes() if p.exists() else None

    def undo(self) -> list[str]:
        """Put back every file the last task wrote or edited. Returns their paths."""
        restored = []
        for p, old in self._backups.items():
            if old is None:
                p.unlink(missing_ok=True)  # the task created it, so remove it
            else:
                p.write_bytes(old)
            restored.append(p.relative_to(self.root).as_posix())
        self._backups = {}
        return sorted(restored)

    # ---------- safety ----------
    def _safe_path(self, path: str) -> Path:
        p = (self.root / path).resolve()
        if p != self.root and self.root not in p.parents:
            raise ToolError(f"'{path}' is outside the workspace; access denied.")
        return p

    # ---------- tools ----------
    def list_files(self, path: str = ".") -> str:
        base = self._safe_path(path)
        if not base.is_dir():
            raise ToolError(f"'{path}' is not a directory.")
        skip = {".git", "__pycache__", "node_modules", ".venv", "venv"}
        lines = []
        for p in sorted(base.rglob("*")):
            if any(part in skip for part in p.relative_to(self.root).parts):
                continue
            rel = p.relative_to(self.root).as_posix()
            lines.append(rel + ("/" if p.is_dir() else ""))
        return _truncate("\n".join(lines) or "(empty)")

    def read_file(self, path: str) -> str:
        p = self._safe_path(path)
        if not p.is_file():
            raise ToolError(f"File '{path}' does not exist.")
        text = p.read_text(encoding="utf-8", errors="replace")
        numbered = "\n".join(f"{i:4}| {line}" for i, line in enumerate(text.splitlines(), 1))
        return _truncate(numbered or "(empty file)")

    def write_file(self, path: str, content: str) -> str:
        p = self._safe_path(path)
        self._backup(p)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"Wrote {len(content)} chars to {path}"

    def edit_file(self, path: str, old: str, new: str) -> str:
        p = self._safe_path(path)
        if not p.is_file():
            raise ToolError(f"File '{path}' does not exist.")
        text = p.read_text(encoding="utf-8")
        count = text.count(old)
        if count == 0:
            raise ToolError("`old` text not found. Read the file again and copy it exactly.")
        if count > 1:
            raise ToolError(f"`old` text appears {count} times; include more context so it is unique.")
        self._backup(p)
        p.write_text(text.replace(old, new, 1), encoding="utf-8")
        return f"Edited {path}"

    def search(self, pattern: str, path: str = ".") -> str:
        base = self._safe_path(path)
        hits = []
        files = [base] if base.is_file() else base.rglob("*")
        for f in files:
            if not f.is_file() or ".git" in f.parts:
                continue
            try:
                for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                    if pattern in line:
                        hits.append(f"{f.relative_to(self.root).as_posix()}:{i}: {line.strip()}")
            except (UnicodeDecodeError, OSError):
                continue  # skip binary/unreadable files
        return _truncate("\n".join(hits) or "No matches.")

    def run_shell(self, command: str) -> str:
        if not self.confirm(command):
            raise ToolError("The user declined to run this command.")
        try:
            r = subprocess.run(command, shell=True, cwd=self.root, capture_output=True,
                               text=True, timeout=self.shell_timeout)
        except subprocess.TimeoutExpired:
            raise ToolError(f"Command timed out after {self.shell_timeout}s.")
        out = f"exit code: {r.returncode}\n--- stdout ---\n{r.stdout}\n--- stderr ---\n{r.stderr}"
        return _truncate(out)

    # ---------- dispatcher ----------
    def run(self, name: str, args: dict) -> str:
        # Only the tools listed in TOOL_SCHEMAS may be called by the model, so it
        # can't call helper methods like undo() or start_task().
        if name not in TOOL_NAMES:
            return f"Error: unknown tool '{name}'."
        fn = getattr(self, name)
        try:
            return fn(**args)
        except ToolError as e:
            return f"Error: {e}"
        except TypeError as e:  # wrong/missing arguments from the model
            return f"Error: bad arguments for {name}: {e}"
        except Exception as e:  # never let a tool crash the agent
            return f"Error: {type(e).__name__}: {e}"


def _fn(name, description, props, required):
    return {"type": "function", "function": {
        "name": name, "description": description,
        "parameters": {"type": "object", "properties": props, "required": required}}}


_S = {"type": "string"}

# JSON schemas the model sees. Clear descriptions = better tool use.
TOOL_SCHEMAS = [
    _fn("list_files", "List all files and folders under a path in the workspace.",
        {"path": {**_S, "description": "Folder path, default '.'"}}, []),
    _fn("read_file", "Read a text file. Returns content with line numbers.",
        {"path": _S}, ["path"]),
    _fn("write_file", "Create a new file or fully overwrite an existing one.",
        {"path": _S, "content": _S}, ["path", "content"]),
    _fn("edit_file", "Replace one exact, unique snippet of text in an existing file. "
        "Prefer this over write_file for small changes.",
        {"path": _S, "old": {**_S, "description": "Exact text to replace"},
         "new": {**_S, "description": "Replacement text"}}, ["path", "old", "new"]),
    _fn("search", "Find lines containing a text pattern across files.",
        {"pattern": _S, "path": {**_S, "description": "Folder or file, default '.'"}}, ["pattern"]),
    _fn("run_shell", "Run a shell command in the workspace (e.g. run tests or a script). "
        "The user must approve each command.",
        {"command": _S}, ["command"]),
]

TOOL_NAMES = {s["function"]["name"] for s in TOOL_SCHEMAS}
