#!/usr/bin/env python3

# ===== IMPORTS ===== #

## ===== STDLIB ===== ##
from __future__ import annotations

from typing import Optional, List, Dict, Any, Iterator, Literal
from importlib.metadata import version, PackageNotFoundError
from dataclasses import dataclass, asdict, field
from contextlib import contextmanager, suppress
import json, os, tempfile, shutil, sys
from time import monotonic, sleep
from pathlib import Path
from enum import Enum
##-##

## ===== 3RD-PARTY ===== ##
##-##

## ===== LOCAL ===== ##
##-##

#-#

# ===== GLOBALS ===== #
def find_project_root() -> Path:
    if (p := os.environ.get("CLAUDE_PROJECT_DIR")): return Path(p)
    cur = Path.cwd()
    for parent in (cur, *cur.parents):
        if (parent / ".claude").exists(): return parent
    print("Error: Could not find project root (no .claude directory).", file=sys.stderr)
    sys.exit(2)

STATE_FILE = PROJECT_ROOT / "sessions" / "sessions-state.json"
LOCK_DIR  = STATE_FILE.with_suffix(".lock")

# Mode description strings
DISCUSSION_MODE_MSG = "You are now in Discussion Mode and should focus on discussing and investigating with the user (no edit-based tools)"
IMPLEMENTATION_MODE_MSG = "You are now in Implementation Mode and may use tools to execute the agreed upon actions - when you are done return immediately to Discussion Mode"
#-#

"""
╔════════════════════════════════════════════════════════════════════════════════════════╗
║ ██████╗██╗  ██╗ █████╗ █████╗ ██████╗█████╗       ██████╗██████╗ █████╗ ██████╗██████╗ ║
║ ██╔═══╝██║  ██║██╔══██╗██╔═██╗██╔═══╝██╔═██╗      ██╔═══╝╚═██╔═╝██╔══██╗╚═██╔═╝██╔═══╝ ║
║ ██████╗███████║███████║█████╔╝█████╗ ██║ ██║      ██████╗  ██║  ███████║  ██║  █████╗  ║
║ ╚═══██║██╔══██║██╔══██║██╔═██╗██╔══╝ ██║ ██║      ╚═══██║  ██║  ██╔══██║  ██║  ██╔══╝  ║
║ ██████║██║  ██║██║  ██║██║ ██║██████╗█████╔╝      ██████║  ██║  ██║  ██║  ██║  ██████╗ ║
║ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝ ╚═╝╚═════╝╚════╝       ╚═════╝  ╚═╝  ╚═╝  ╚═╝  ╚═╝  ╚═════╝ ║
╚════════════════════════════════════════════════════════════════════════════════════════╝
SharedState Module

Provides centralized state management for hooks:
- DAIC mode tracking and toggling
- Task state persistence  
- Active todo list management
- Project root detection

Release note (v0.3.0):
So ppl are already asking about paralellism so we're going to maybe make this less pain in the dik by providing some locking and atomic writing despite not really needing it for the main thread rn. If it becomes super annoying then multi-session bros will have to take ritalin.
"""

# ===== DECLARATIONS ===== #

## ===== EXCEPTIONS ===== ##
class StateError(RuntimeError): pass

class StashOccupiedError(RuntimeError): pass
##-##

## ===== ENUMS ===== ##
class Mode(str, Enum):
    NO = "discussion"
    GO = "implementation"

class TodoStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"

class Model(str, Enum):
    OPUS = "opus"
    SONNET = "sonnet"
##-##

## ===== DATA CLASSES ===== ##

#!> State components
@dataclass
class TaskState:
    name: Optional[str] = None
    file: Optional[str] = None
    branch: Optional[str] = None
    status: Optional[str] = None
    created: Optional[str] = None
    started: Optional[str] = None
    updated: Optional[str] = None
    submodules: Optional[List[str]] = None

    @property
    def file_path(self) -> Optional[Path]:
        if not self.file: return None
        file_path = PROJECT_ROOT / 'sessions' / 'tasks' / self.file
        if file_path.exists(): return file_path

    @property
    def task_state(self) -> Dict[str, Any]:
        d = asdict(self)
        return d

    @classmethod
    def load_task(cls, path: Path) -> "TaskState":
        tasks_root = PROJECT_ROOT / 'sessions' / 'tasks'
        if not path.exists(): raise FileNotFoundError(f"Task file {path} does not exist.")
        # Parse task file frontmatter into fields
        content = path.read_text(encoding="utf-8")
        if not (fm_start := content.find("---")) == 0: raise StateError(f"Task file {path} missing frontmatter.")
        fm_end = content.find("---", fm_start + 3)
        if fm_end == -1: raise StateError(f"Task file {path} missing frontmatter end.")
        fm_content = content[fm_start + 3:fm_end].strip()
        data = {}
        for line in fm_content.splitlines():
            if ':' not in line: continue
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            if key == "submodules": data[key] = [s.strip() for s in value.split(',') if s.strip()]
            else: data[key] = value or None
        try: rel = path.relative_to(tasks_root); data["file"] = str(rel)
        except ValueError: data["file"] = path.name
        return cls(**data)

@dataclass
class CCTodo:
    content: str
    status: TodoStatus = TodoStatus.PENDING
    activeForm: Optional[str] = None


@dataclass
class SessionsFlags:
    context_85: bool = False
    context_90: bool = False
    subagent: bool = False
    noob: bool = True

    def clear_flags(self) -> None:
        self.context_85 = False
        self.context_90 = False
        self.subagent = False

@dataclass
class SessionsTodos:
    active: List[CCTodo] = field(default_factory=list)
    stashed: List[CCTodo] = field(default_factory=list)

    def store_todos(self, todos: List[Dict[str, str]], over: bool = True) -> bool:
        """
        Store a list of todos (dicts with 'content', activeForm, and optional 'status') into active.
        Returns True if any were added, False if none.
        """
        if self.active:
            if not over: return False
            self.clear_active()
        try:
            for t in todos:
                self.active.append(CCTodo(
                    content=t.get('content', ''),
                    activeForm=t.get('activeForm'),
                    status=TodoStatus(t.get('status', 'pending')) if 'status' in t else TodoStatus.PENDING))
            return True
        except Exception as e: print(f"Error loading todos: {e}"); return False

    def all_complete(self) -> bool:
        """True if every active todo is COMPLETED (ignores stashed)."""
        return all(t.status is TodoStatus.COMPLETED for t in self.active)

    def stash_active(self, *, force: bool = True) -> int:
        """
        Move the entire active set into the single stash slot, clearing active.
        Overwrites any stashed todos unless force = False (which raises StashOccupiedError).
        Returns number moved.
        """
        if not self.stashed or force:
            n = len(self.active)
            self.stashed = list(self.active)
            self.active.clear()
            return n
        raise StashOccupiedError("Stash already occupied. Use force=True to overwrite.")

    def clear_active(self) -> int:
        """Delete all active todos. Returns number removed."""
        n = len(self.active)
        self.active.clear()
        return n

    def clear_stashed(self) -> int:
        """Delete all stashed todos. Returns number removed."""
        n = len(self.stashed)
        self.stashed.clear()
        return n

    def restore_stashed(self) -> int:
        """
        Restore the stashed set back into active *only if* the active set is
        complete or empty. Replaces active (does not append). Returns number restored.
        If stash is empty, returns 0 and does nothing.
        """
        if not self.stashed: return 0
        if self.active and not self.all_complete(): return 0
        n = len(self.stashed)
        self.active.clear()
        self.active.extend(self.stashed)
        self.stashed.clear()
        return n

    def to_list(self, which: Literal['active', 'stashed']) -> List[Dict[str, str]]:
        """Return the specified todo list as a list of dicts."""
        if which == 'active': out = [asdict(t) for t in self.active]
        elif which == 'stashed': out = [asdict(t) for t in self.stashed]
        else: raise ValueError("which must be 'active' or 'stashed'")

        for t in out:
            if isinstance(t.get("status"), Enum): t["status"] = t["status"].value
        return out

    def list_content(self, which: Literal['active', 'stashed']) -> List[str]:
        """Return a list of the content strings of all active todos."""
        todos = self.active if which == 'active' else self.stashed
        return [t.content for t in todos]

#!<

#!> State object
@dataclass
class SessionsState:
    version: str = "unknown"
    current_task: TaskState = field(default_factory=TaskState)
    mode: Mode = Mode.NO
    todos: SessionsTodos = field(default_factory=SessionsTodos)
    model: Model = Model.OPUS
    flags: SessionsFlags = field(default_factory=SessionsFlags)
    # freeform bag for runtime-only / unknown keys:
    metadata: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def _coerce_todo(x: Any) -> CCTodo:
        if isinstance(x, str): return CCTodo(x)
        status = x.get("status", TodoStatus.PENDING)
        if isinstance(status, str): status = TodoStatus(status)
        return CCTodo(content=x.get("content", ""), status=status)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SessionsState":
        try: pkg_version = version("cc-sessions")
        except PackageNotFoundError: pkg_version = "unknown"
        return cls(
            version=d.get("version", pkg_version),
            current_task=TaskState(**d.get("current_task", {})),
            mode=Mode(d.get("mode", Mode.NO)),
            todos=SessionsTodos(
                active=[cls._coerce_todo(t) for t in d.get("todos", {}).get("active", [])],
                stashed=[cls._coerce_todo(t) for t in d.get("todos", {}).get("stashed", [])],
            ),
            model=Model(d.get("model") or Model.OPUS),
            flags=SessionsFlags(
                context_85=d.get("flags", {}).get("context_85") or d.get("flags", {}).get("context_warnings", {}).get("85%", False),
                context_90=d.get("flags", {}).get("context_90") or d.get("flags", {}).get("context_warnings", {}).get("90%", False),
                subagent=d.get("flags", {}).get("subagent", False),
            ),
            metadata=d.get("metadata", {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["mode"] = self.mode.value
        # Normalize enums in nested todos for JSON
        for bucket in ("active", "stashed"):
            for t in d["todos"][bucket]:
                if isinstance(t.get("status"), Enum): t["status"] = t["status"].value
        return d
#!<

##-##

#-#

# ===== FUNCTIONS ===== #

## ===== STATE PROTECTION ===== ##
def _the_ol_in_out(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=str(path.parent), encoding="utf-8") as tmp:
        json.dump(obj, tmp, indent=2)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_name = tmp.name
    os.replace(tmp_name, path)  # atomic across filesystems on same volume

@contextmanager
def _lock(lock_dir: Path, timeout: float = 5.0, poll: float = 0.05) -> Iterator[None]:
    start = monotonic()
    while True:
        try:
            lock_dir.mkdir(exist_ok=False)  # atomic lock acquire
            break
        except FileExistsError:
            if monotonic() - start > timeout:
                raise TimeoutError(f"Could not acquire lock {lock_dir} in {timeout}s")
            sleep(poll)
    try:
        yield
    finally:
        with suppress(Exception):
            shutil.rmtree(lock_dir)
##-##

## ===== GEIPI ===== ##
def load_state() -> SessionsState:
    if not STATE_FILE.exists():
        initial = SessionsState()
        _the_ol_in_out(STATE_FILE, initial.to_dict())
        return initial
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        # Corrupt file: back it up once and start fresh
        backup = STATE_FILE.with_suffix(".bad.json")
        with suppress(Exception):
            STATE_FILE.replace(backup)
        fresh = SessionsState()
        _the_ol_in_out(STATE_FILE, fresh.to_dict())
        return fresh
    return SessionsState.from_dict(data)

@contextmanager
def edit_state() -> Iterator[SessionsState]:
    # Acquire lock, reload (so we operate on latest), yield, then save atomically
    with _lock(LOCK_DIR):
        state = load_state()
        try: yield state
        except Exception: raise
        else: _the_ol_in_out(STATE_FILE, state.to_dict())
##-##

#-#
