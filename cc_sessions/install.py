#!/usr/bin/env python3

# ===== IMPORTS ===== #

## ===== STDLIB ===== ##
import shutil, json, sys, os, subprocess, tempfile, contextlib, re, io, builtins
from pathlib import Path
from time import sleep
##-##

## ===== 3RD-PARTY ===== ##
from inquirer import themes
import platform
import inquirer
##-##

## ===== LOCAL ===== ##
##-##

#-#

# ===== GLOBALS ===== #
# Global shared_state handle (set after files are installed)
ss = None

# Standard agents we ship and may import overrides for
AGENT_BASELINE = [
    'code-review.md',
    'context-gathering.md',
    'context-refinement.md',
    'logging.md',
    'service-documentation.md',
]

# ===== TUI + Inquirer wrappers (j/k navigation) ===== #
PADDING_TOP = 1
PADDING_LEFT = 3
# Top padding inside the body pane for prompts/logs
BODY_TOP_PAD = 0

_TUI_ACTIVE = False
_TUI = None  # type: ignore
try: import curses; _CURSES_AVAILABLE = True
except Exception: _CURSES_AVAILABLE = False

_ORIG_LIST_INPUT = getattr(inquirer, 'list_input', None)
_ORIG_CHECKBOX = getattr(inquirer, 'checkbox', None)
_ORIG_INPUT = builtins.input

_ANSI_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
def _strip_ansi(s):
    try: return _ANSI_RE.sub('', s)
    except Exception:
        try: return str(s)
        except Exception: return ''

#-#

"""
╔═════════════════════════════════════════════════════════════════════╗
║ ██████╗██╗  ██╗██████╗██████╗ █████╗ ██╗     ██╗     ██████╗█████╗  ║
║ ╚═██╔═╝███╗ ██║██╔═══╝╚═██╔═╝██╔══██╗██║     ██║     ██╔═══╝██╔═██╗ ║
║   ██║  ████╗██║██████╗  ██║  ███████║██║     ██║     █████╗ █████╔╝ ║
║   ██║  ██╔████║╚═══██║  ██║  ██╔══██║██║     ██║     ██╔══╝ ██╔═██╗ ║
║ ██████╗██║╚███║██████║  ██║  ██║  ██║███████╗███████╗██████╗██║ ██║ ║
║ ╚═════╝╚═╝ ╚══╝╚═════╝  ╚═╝  ╚═╝  ╚═╝╚══════╝╚══════╝╚═════╝╚═╝ ╚═╝ ║
╚═════════════════════════════════════════════════════════════════════╝
cc-sessions installer module for pip/pipx installation.
This module is imported and executed when running `cc-sessions` command.
"""

# ===== DECLARATIONS ===== #

## ===== ENUMS ===== ##
# Colors for terminal output
class Colors:
    RESET = '\033[0m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    CYAN = '\033[36m'
    GRAY = '\033[38;5;240m'
    BOLD = '\033[1m'
##-##

#-#

# ===== CLASSES ===== #
class TuiManager:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.header_lines = []
        self.legend = ''
        self.log = []
        self.in_prompt = False
        self.info_lines: list[str] = []
        self._pair_map: dict[int, int] = {}
        self._next_pair_id = 10
        # Initialize colors
        try:
            curses.start_color()
            try: curses.use_default_colors()
            except Exception: pass
            curses.init_pair(1, curses.COLOR_GREEN, -1)
            curses.init_pair(2, curses.COLOR_CYAN, -1)
            curses.init_pair(3, curses.COLOR_YELLOW, -1)
            curses.init_pair(4, curses.COLOR_RED, -1)
            curses.init_pair(5, curses.COLOR_BLACK, -1)
        except Exception:
            pass
        self._build_windows()

    def _calc_header_h(self, total_h):
        footer_h = 1
        min_body = 6
        max_header = max(3, total_h - footer_h - min_body)
        # Include vertical top padding for header content
        needed = max(3, len(self.header_lines) + PADDING_TOP)
        return min(needed, max_header)

    def _build_windows(self, header_h=None):
        self.stdscr.clear()
        self.stdscr.refresh()
        h, w = self.stdscr.getmaxyx()
        if header_h is None:
            header_h = self._calc_header_h(h)
        footer_h = 1
        body_h = max(1, h - header_h - footer_h)
        self.header_win = curses.newwin(header_h, w, 0, 0)
        self.body_win = curses.newwin(body_h, w, header_h, 0)
        self.footer_win = curses.newwin(footer_h, w, header_h + body_h, 0)
        self.redraw_all()

    def set_header(self, lines):
        self.header_lines = [str(x) for x in lines]
        # Resize header to fit content, preserving minimum body height
        try:
            total_h, _ = self.stdscr.getmaxyx()
            desired = self._calc_header_h(total_h)
            current = self.header_win.getmaxyx()[0]
            # Only grow, never shrink header height within a session to avoid jumping
            if desired > current:
                self._build_windows(desired)
            else:
                self.redraw_header()
        except Exception:
            self.redraw_header()

    def set_legend(self, txt):
        self.legend = txt or ''
        self.redraw_footer()

    def set_info(self, lines: list[str] | None):
        self.info_lines = [str(x) for x in (lines or [])]
        # When not in a prompt, refresh body to show info
        if not self.in_prompt:
            self.redraw_body(mode='log')

    def clear_info(self):
        self.set_info([])

    def log_line(self, line):
        if self.in_prompt:
            self.log.append(line)
            return
        self.log.append(line)
        self.redraw_body(mode='log')

    def clear_body(self):
        self.body_win.erase()
        self.body_win.refresh()

    def redraw_header(self):
        self.header_win.erase()
        max_h, max_w = self.header_win.getmaxyx()
        # Respect PADDING_TOP at the top of the header window
        max_lines = max_h - PADDING_TOP
        for i, raw in enumerate(self.header_lines[: max_lines]):
            try:
                self._addstr_ansi(self.header_win, PADDING_TOP + i, PADDING_LEFT, raw, width=max_w - PADDING_LEFT - 1)
            except Exception:
                pass
        self.header_win.refresh()

    def redraw_footer(self):
        self.footer_win.erase()
        text = self.legend or ''
        try:
            # Apply consistent side padding for legend
            max_w = self.footer_win.getmaxyx()[1]
            self.footer_win.addstr(0, PADDING_LEFT, text[: max_w - PADDING_LEFT - 1])
        except Exception:
            pass
        self.footer_win.refresh()

    def redraw_body(self, mode='log', list_state=None):
        self.body_win.erase()
        h, w = self.body_win.getmaxyx()
        if mode == 'log':
            # Show info lines first, then recent log lines below
            y = BODY_TOP_PAD
            for il in self.info_lines:
                try:
                    self._addstr_ansi(self.body_win, y, PADDING_LEFT, il, width=w - PADDING_LEFT - 1)
                except Exception:
                    pass
                y += 1

            usable = max(0, h - y)
            start = max(0, len(self.log) - usable)
            visible = self.log[start: start + usable]
            for i, line in enumerate(visible):
                try:
                    self._addstr_ansi(self.body_win, y + i, PADDING_LEFT, line, width=w - PADDING_LEFT - 1)
                except Exception:
                    pass
        elif mode == 'list' and list_state:
            title, options, idx, scroll = list_state
            y = BODY_TOP_PAD
            for il in self.info_lines:
                try: self._addstr_ansi(self.body_win, y, PADDING_LEFT, il, width=w - PADDING_LEFT - 1)
                except Exception: pass
                y += 1
            try: self._addstr_ansi(self.body_win, y, PADDING_LEFT, title, width=w - PADDING_LEFT - 1)
            except Exception: pass
            max_visible = max(1, h - (y + 2))
            if idx < scroll: scroll = idx
            elif idx >= scroll + max_visible: scroll = idx - max_visible + 1
            for i in range(scroll, min(len(options), scroll + max_visible)):
                disp = options[i]
                prefix = '> ' if i == idx else '  '
                text = f"{prefix}{disp}"
                try:
                    row = y + 1 + i - scroll
                    if i == idx:
                        self._addstr_ansi(self.body_win, row, PADDING_LEFT, text, width=w - PADDING_LEFT - 1, attr_extra=curses.A_BOLD)
                    else:
                        self._addstr_ansi(self.body_win, row, PADDING_LEFT, text, width=w - PADDING_LEFT - 1)
                except Exception: pass
        elif mode == 'checkbox' and list_state:
            title, options, checked_set, idx, scroll = list_state
            y = BODY_TOP_PAD
            for il in self.info_lines:
                try: self._addstr_ansi(self.body_win, y, PADDING_LEFT, il, width=w - PADDING_LEFT - 1)
                except Exception: pass
                y += 1
            try: self._addstr_ansi(self.body_win, y, PADDING_LEFT, title, width=w - PADDING_LEFT - 1)
            except Exception: pass
            max_visible = max(1, h - (y + 2))
            if idx < scroll: scroll = idx
            elif idx >= scroll + max_visible: scroll = idx - max_visible + 1
            for i in range(scroll, min(len(options), scroll + max_visible)):
                disp = options[i]
                mark = '[x]' if options[i] in checked_set else '[ ]'
                pointer = '> ' if i == idx else '  '
                text = f"{pointer}{mark} {disp}"
                try:
                    row = y + 1 + i - scroll
                    if i == idx:
                        self._addstr_ansi(self.body_win, row, PADDING_LEFT, text, width=w - PADDING_LEFT - 1, attr_extra=curses.A_BOLD)
                    else:
                        self._addstr_ansi(self.body_win, row, PADDING_LEFT, text, width=w - PADDING_LEFT - 1)
                except Exception: pass
        self.body_win.refresh()

    def resize(self):
        curses.update_lines_cols()
        total_h, _ = self.stdscr.getmaxyx()
        footer_h = 1
        min_body = 6
        allowed_max = max(3, total_h - footer_h - min_body)
        current = self.header_win.getmaxyx()[0]
        new_h = min(current, allowed_max)
        self._build_windows(new_h)

    def list_prompt(self, message, choices, default=None):
        self.in_prompt = True
        opts = list(choices)
        idx = 0
        if default is not None:
            try: idx = opts.index(default)
            except Exception: pass
        scroll = 0
        self.set_legend('j/k or arrows • Enter select • Ctrl+C exit')
        title = message if isinstance(message, str) else str(message)
        while True:
            self.redraw_body(mode='list', list_state=(title, opts, idx, scroll))
            key = self.stdscr.getch()
            if key == curses.KEY_RESIZE:
                self.resize(); continue
            if key in (curses.KEY_UP, ord('k')): idx = (idx - 1) % len(opts)
            elif key in (curses.KEY_DOWN, ord('j')): idx = (idx + 1) % len(opts)
            elif key in (curses.KEY_ENTER, 10, 13):
                self.in_prompt = False
                self.set_legend('')
                self.redraw_body(mode='log')
                return opts[idx]
            elif key in (3, 27):
                self.in_prompt = False
                self.set_legend('')
                self.redraw_body(mode='log')
                raise KeyboardInterrupt

    def checkbox_prompt(self, message, choices, default=None):
        self.in_prompt = True
        opts = list(choices)
        checked = set(default or [])
        def _is_checked(item):
            return item in checked or _strip_ansi(str(item)) in checked
        checked_set = set(o for o in opts if _is_checked(o))
        idx = 0
        scroll = 0
        self.set_legend('j/k or arrows • Space toggle • Enter submit • Ctrl+C exit')
        title = message if isinstance(message, str) else str(message)
        while True:
            self.redraw_body(mode='checkbox', list_state=(title, opts, checked_set, idx, scroll))
            key = self.stdscr.getch()
            if key == curses.KEY_RESIZE:
                self.resize(); continue
            if key in (curses.KEY_UP, ord('k')): idx = (idx - 1) % len(opts)
            elif key in (curses.KEY_DOWN, ord('j')): idx = (idx + 1) % len(opts)
            elif key in (ord(' '),):
                cur = opts[idx]
                if cur in checked_set: checked_set.remove(cur)
                else: checked_set.add(cur)
            elif key in (curses.KEY_ENTER, 10, 13):
                self.in_prompt = False
                self.set_legend('')
                self.redraw_body(mode='log')
                return [o for o in opts if o in checked_set]
            elif key in (3, 27):
                self.in_prompt = False
                self.set_legend('')
                self.redraw_body(mode='log')
                raise KeyboardInterrupt

    def text_input(self, prompt: str) -> str:
        self.in_prompt = True
        self.set_legend('Type • Enter submit • Ctrl+C cancel')
        buf = ''
        title = prompt if isinstance(prompt, str) else str(prompt)
        while True:
            self.body_win.erase()
            h, w = self.body_win.getmaxyx()
            y = BODY_TOP_PAD
            for il in self.info_lines:
                try: self._addstr_ansi(self.body_win, y, PADDING_LEFT, il, width=w - PADDING_LEFT - 1)
                except Exception: pass
                y += 1
            try: self._addstr_ansi(self.body_win, y, PADDING_LEFT, title, width=w - PADDING_LEFT - 1)
            except Exception: pass
            line = buf + '_'
            try: self._addstr_ansi(self.body_win, y + 1, PADDING_LEFT, line, width=w - PADDING_LEFT - 1)
            except Exception: pass
            self.body_win.refresh()
            ch = self.stdscr.getch()
            if ch == curses.KEY_RESIZE:
                self.resize(); continue
            if ch in (10, 13):
                self.in_prompt = False
                self.set_legend('')
                self.redraw_body(mode='log')
                return buf
            if ch in (3, 27):
                self.in_prompt = False
                self.set_legend('')
                self.redraw_body(mode='log')
                raise KeyboardInterrupt
            if ch in (curses.KEY_BACKSPACE, 127, 8):
                buf = buf[:-1]
            elif 0 <= ch < 256:
                buf += chr(ch)

    def redraw_all(self):
        self.redraw_header(); self.redraw_body(mode='log'); self.redraw_footer()

    def _addstr_ansi(self, win, y, x, text, *, width=None, attr_extra=0):
        """Render a string with basic ANSI SGR (color/bold) into a curses window."""
        if text is None: return
        s = str(text)
        pattern = re.compile(r"\x1b\[([0-9;]*)m")
        pos = 0
        col = x
        max_w = win.getmaxyx()[1]
        if width is None: width = max_w - x - 1
        cur_color = 0
        bold = False
        dim = False
        base_attr = curses.A_NORMAL
        def get_attr():
            attr = base_attr
            if cur_color:
                attr |= curses.color_pair(cur_color)
            if bold:
                attr |= curses.A_BOLD
            if dim:
                try: attr |= curses.A_DIM
                except Exception: pass
            if attr_extra:
                attr |= attr_extra
            return attr
        for m in pattern.finditer(s):
            chunk = s[pos:m.start()]
            if chunk:
                remain = width - (col - x)
                if remain <= 0: break
                out = chunk[:remain]
                try: win.addstr(y, col, out, get_attr())
                except Exception: pass
                col += len(out)
            params = m.group(1)
            # Support 256-color form 38;5;N
            had_256 = False
            if params:
                for mm in re.finditer(r'(?:^|;)38;5;(\d+)(?=;|$)', params):
                    try:
                        col_idx = int(mm.group(1))
                        cur_color = self._pair_for_256(col_idx)
                        had_256 = True
                    except Exception:
                        pass
                # Remove any 38;5;N segments so the remaining split doesn't misinterpret
                params = re.sub(r'(?:^|;)38;5;\d+(?=;|$)', '', params).strip(';')
            if not params:
                # If we only had a 256-color code, keep the chosen color (don't reset)
                if not had_256:
                    cur_color = 0; bold = False; dim = False
            else:
                for code in params.split(';'):
                    if not code: continue
                    try: n = int(code)
                    except ValueError: continue
                    if n == 0:
                        cur_color = 0; bold = False; dim = False
                    elif n == 1:
                        bold = True
                    elif n in (22,):
                        bold = False
                    elif n == 31:
                        cur_color = 4  # red pair
                    elif n == 32:
                        cur_color = 1  # green pair
                    elif n == 33:
                        cur_color = 3  # yellow pair
                    elif n == 36:
                        cur_color = 2  # cyan pair
                    elif n == 90:
                        # bright black (gray). Use black + dim to approximate gray
                        cur_color = 5; dim = True
                    elif n == 39:
                        cur_color = 0; dim = False
            pos = m.end()
        chunk = s[pos:]
        if chunk and (col - x) < width:
            out = chunk[: width - (col - x)]
            try: win.addstr(y, col, out, get_attr())
            except Exception: pass

    def _pair_for_256(self, color_idx: int) -> int:
        try:
            if color_idx in self._pair_map:
                return self._pair_map[color_idx]
            # Only attempt if terminal supports many colors
            if hasattr(curses, 'COLORS') and curses.COLORS >= 256:
                pair_id = self._next_pair_id
                # Avoid exceeding available pairs
                if hasattr(curses, 'COLOR_PAIRS') and pair_id >= curses.COLOR_PAIRS:
                    return 0
                curses.init_pair(pair_id, color_idx, -1)
                self._pair_map[color_idx] = pair_id
                self._next_pair_id += 1
                return pair_id
        except Exception:
            pass
        # Fallback to cyan dim as a neutral-ish shade if unsupported
        return 2

class _TuiWriter:
    def __init__(self, manager):
        self.mgr = manager
        self._buf = ''
    def write(self, s):
        if not s: return 0
        self._buf += str(s)
        while '\n' in self._buf:
            line, self._buf = self._buf.split('\n', 1)
            # Keep ANSI so TUI can render colors
            self.mgr.log_line(line)
        return len(s)
    def flush(self):
        if self._buf:
            self.mgr.log_line(self._buf)
            self._buf = ''

class _TuiSession:
    def __init__(self):
        self._orig_out = sys.stdout
        self._orig_err = sys.stderr
        self._orig_input = builtins.input
    def __enter__(self):
        global _TUI_ACTIVE, _TUI
        if not _CURSES_AVAILABLE or not sys.stdin.isatty():
            _TUI_ACTIVE = False
            return self
        stdscr = curses.initscr()
        curses.noecho(); curses.cbreak(); stdscr.keypad(True)
        try: curses.curs_set(0)
        except Exception: pass
        try:
            curses.start_color()
            try: curses.use_default_colors()
            except Exception: pass
        except Exception:
            pass
        _TUI_ACTIVE = True
        _TUI = TuiManager(stdscr)
        sys.stdout = _TuiWriter(_TUI)
        sys.stderr = _TuiWriter(_TUI)
        builtins.input = lambda prompt='': _TUI.text_input(prompt)
        return self
    def __exit__(self, exc_type, exc, tb):
        global _TUI_ACTIVE, _TUI
        try:
            if _TUI_ACTIVE and _TUI is not None:
                try: curses.curs_set(1)
                except Exception: pass
                curses.nocbreak(); _TUI.stdscr.keypad(False); curses.echo(); curses.endwin()
        finally:
            sys.stdout = self._orig_out
            sys.stderr = self._orig_err
            builtins.input = self._orig_input
            _TUI_ACTIVE = False
            _TUI = None
#-#

# ===== FUNCTIONS ===== #

## ===== UTILITIES ===== ##
def copy_file(src, dest):
    if src.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)

        # Preserve executable permissions
        try:
            src_mode = src.stat().st_mode
            dest.chmod(src_mode)
        except Exception:
            # Ignore chmod errors
            pass

def copy_directory(src, dest):
    if not src.exists():
        return

    dest.mkdir(parents=True, exist_ok=True)

    for item in src.iterdir():
        src_path = src / item.name
        dest_path = dest / item.name

        if item.is_dir():
            copy_directory(src_path, dest_path)
        else:
            copy_file(src_path, dest_path)

def _files_differ(src: Path, dest: Path) -> bool:
    try:
        if not dest.exists():
            return True
        if src.stat().st_size != dest.stat().st_size:
            return True
        return src.read_bytes() != dest.read_bytes()
    except Exception:
        return True

def copy_agents_if_changed(src_root: Path, dest_root: Path) -> tuple[int, int]:
    """Copy agent files if content differs. Returns (copied, skipped_identical)."""
    copied = 0
    skipped = 0
    if not src_root.exists():
        return (0, 0)
    for p in src_root.rglob('*'):
        if not p.is_file():
            continue
        rel = p.relative_to(src_root)
        dst = dest_root / rel
        if _files_differ(p, dst):
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dst)
            try:
                dst.chmod(p.stat().st_mode)
            except Exception:
                pass
            copied += 1
        else:
            skipped += 1
    return (copied, skipped)

def color(text, color_code) -> str:
    return f"{color_code}{text}{Colors.RESET}"

def fmt_msg(text: str) -> str:
    """Normalize prompt text and add cyan color.
    - Collapses duplicate trailing colons to a single colon
    - Applies cyan color for interactive prompts
    """
    if not isinstance(text, str):
        return text
    s = text.rstrip()
    # Collapse multiple trailing colons to one
    while s.endswith('::'):
        s = s[:-1]
    return color(s, Colors.CYAN)

def choices_filtered(choices):
    """Filter out falsy/None choices for inquirer inputs."""
    return [c for c in choices if c]

def capture_header(printer_fn) -> list[str]:
    buf = io.StringIO()
    orig = sys.stdout
    try:
        sys.stdout = buf
        printer_fn()
    finally:
        sys.stdout = orig
    content = buf.getvalue()
    # Keep ANSI so TUI can render colors in header
    lines = [line.rstrip('\n') for line in content.splitlines()]
    return lines

def show_header(printer_fn) -> None:
    if _TUI_ACTIVE and _TUI is not None:
        try:
            _TUI.set_header(capture_header(printer_fn))
        except Exception:
            # If capture fails, fall back to printing
            printer_fn()
    else:
        printer_fn()

def set_info(lines: list[str]) -> None:
    if _TUI_ACTIVE and _TUI is not None:
        _TUI.set_info(lines)
    else:
        for ln in lines:
            print(ln)

def clear_info() -> None:
    if _TUI_ACTIVE and _TUI is not None:
        _TUI.clear_info()

def get_package_root() -> Path: return Path(__file__).parent

def get_project_root() -> Path: return Path.cwd()

def tui_session(): return _TuiSession()

def _jk_list_input(message: str, choices, default=None):
    if _TUI_ACTIVE and _TUI is not None: return _TUI.list_prompt(message, choices, default)
    if not _CURSES_AVAILABLE or not sys.stdin.isatty() or _ORIG_LIST_INPUT is None: return _ORIG_LIST_INPUT(message=message, choices=choices, default=default)

    def _run(stdscr):
        curses.curs_set(0)
        stdscr.keypad(True)
        height, width = stdscr.getmaxyx()
        title = message if isinstance(message, str) else str(message)
        opts = list(choices)
        disp_opts = [_strip_ansi(str(x)) for x in opts]
        idx = 0
        if default is not None:
            try: idx = opts.index(default)
            except Exception: pass
        scroll = 0
        max_visible = max(3, height - 4)

        while True:
            stdscr.clear()
            stdscr.addstr(0, 0, title[:width-1])
            stdscr.addstr(1, 0, "Use j/k or arrows • Enter to select • Ctrl+C to exit")

            if idx < scroll: scroll = idx
            elif idx >= scroll + max_visible: scroll = idx - max_visible + 1

            for i in range(scroll, min(len(opts), scroll + max_visible)):
                disp = disp_opts[i]
                prefix = '> ' if i == idx else '  '
                text = f"{prefix}{disp}"
                if i == idx: stdscr.addstr(2 + i - scroll, 0, text[:width-1], curses.A_BOLD)
                else: stdscr.addstr(2 + i - scroll, 0, text[:width-1])

            key = stdscr.getch()
            if key in (curses.KEY_UP, ord('k')): idx = (idx - 1) % len(opts)
            elif key in (curses.KEY_DOWN, ord('j')): idx = (idx + 1) % len(opts)
            elif key in (curses.KEY_ENTER, 10, 13): return opts[idx]
            elif key in (3, 27): raise KeyboardInterrupt

    return curses.wrapper(_run)

def _jk_checkbox(message: str, choices, default=None):
    if _TUI_ACTIVE and _TUI is not None: return _TUI.checkbox_prompt(message, choices, default)
    if not _CURSES_AVAILABLE or not sys.stdin.isatty() or _ORIG_CHECKBOX is None: return _ORIG_CHECKBOX(message=message, choices=choices, default=default)

    def _run(stdscr):
        curses.curs_set(0)
        stdscr.keypad(True)
        height, width = stdscr.getmaxyx()
        title = message if isinstance(message, str) else str(message)
        opts = list(choices)
        disp_opts = [_strip_ansi(str(x)) for x in opts]
        checked = set(default or [])
        idx = 0
        scroll = 0
        max_visible = max(3, height - 5)
        legend = "j/k or arrows move • Space toggles • Enter submit • Ctrl+C exits"

        while True:
            stdscr.clear()
            stdscr.addstr(0, 0, title[:width-1])
            stdscr.addstr(1, 0, legend[:width-1])

            if idx < scroll: scroll = idx
            elif idx >= scroll + max_visible: scroll = idx - max_visible + 1

            for i in range(scroll, min(len(opts), scroll + max_visible)):
                line = opts[i]
                disp = disp_opts[i]
                mark = '[x]' if line in checked else '[ ]'
                pointer = '> ' if i == idx else '  '
                text = f"{pointer}{mark} {disp}"
                if i == idx: stdscr.addstr(2 + i - scroll, 0, text[:width-1], curses.A_BOLD)
                else: stdscr.addstr(2 + i - scroll, 0, text[:width-1])

            key = stdscr.getch()
            if key in (curses.KEY_UP, ord('k')): idx = (idx - 1) % len(opts)
            elif key in (curses.KEY_DOWN, ord('j')): idx = (idx + 1) % len(opts)
            elif key in (ord(' '),):
                cur = opts[idx]
                if cur in checked: checked.remove(cur)
                else: checked.add(cur)
            elif key in (curses.KEY_ENTER, 10, 13): return [o for o in opts if o in checked]
            elif key in (3, 27): raise KeyboardInterrupt

    return curses.wrapper(_run)

try:
    if _ORIG_LIST_INPUT is not None: inquirer.list_input = _jk_list_input  # type: ignore
    if _ORIG_CHECKBOX is not None: inquirer.checkbox = _jk_checkbox  # type: ignore
except Exception: pass


##-##

## ===== ASCII BANNERS ===== ##

#!> Main header
def print_installer_header() -> None:
    print()
    print(color('╔════════════════════════════════════════════════════════════╗', Colors.GREEN))
    print(color('║ ██████╗██████╗██████╗██████╗██████╗ █████╗ ██╗  ██╗██████╗ ║', Colors.GREEN))
    print(color('║ ██╔═══╝██╔═══╝██╔═══╝██╔═══╝╚═██╔═╝██╔══██╗███╗ ██║██╔═══╝ ║',Colors.GREEN))
    print(color('║ ██████╗█████╗ ██████╗██████╗  ██║  ██║  ██║████╗██║██████╗ ║',Colors.GREEN))
    print(color('║ ╚═══██║██╔══╝ ╚═══██║╚═══██║  ██║  ██║  ██║██╔████║╚═══██║ ║',Colors.GREEN))
    print(color('║ ██████║██████╗██████║██████║██████╗╚█████╔╝██║╚███║██████║ ║',Colors.GREEN))
    print(color('║ ╚═════╝╚═════╝╚═════╝╚═════╝╚═════╝ ╚════╝ ╚═╝ ╚══╝╚═════╝ ║',Colors.GREEN)) 
    print(color('╚════════╗  an opinionated approach to productive  ╔═════════╝',Colors.GREEN))
    print(color('         ╚═══   development with Claude Code   ════╝',Colors.GREEN))
    print()
    print()
#!<

#!> Configuration header
def print_config_header() -> None:
    print()
    print(color('╔══════════════════════════════════════════════╗',Colors.GREEN))
    print(color('║  █████╗ █████╗ ██╗  ██╗██████╗██████╗ █████╗ ║',Colors.GREEN))
    print(color('║ ██╔═══╝██╔══██╗███╗ ██║██╔═══╝╚═██╔═╝██╔═══╝ ║',Colors.GREEN))
    print(color('║ ██║    ██║  ██║████╗██║█████╗   ██║  ██║     ║',Colors.GREEN))
    print(color('║ ██║    ██║  ██║██╔████║██╔══╝   ██║  ██║ ██╗ ║',Colors.GREEN))
    print(color('║ ╚█████╗╚█████╔╝██║╚███║██║    ██████╗╚█████║ ║',Colors.GREEN))
    print(color('║  ╚════╝ ╚════╝ ╚═╝ ╚══╝╚═╝    ╚═════╝ ╚════╝ ║',Colors.GREEN))
    print(color('╚════════════ quick config editor ═════════════╝',Colors.GREEN))
    print()
    print()
#!<

#!> Git preferences header
def print_git_section(editor: bool = False) -> None:
    print()
    print(color('╔═════════════════════════════════════════════╗', Colors.GREEN))
    print(color('║ ██████╗ █████╗ ██╗ ██╗█████╗  █████╗██████╗ ║', Colors.GREEN))
    print(color('║ ██╔═══╝██╔══██╗██║ ██║██╔═██╗██╔═══╝██╔═══╝ ║', Colors.GREEN))
    print(color('║ ██████╗██║  ██║██║ ██║█████╔╝██║    █████╗  ║', Colors.GREEN))
    print(color('║ ╚═══██║██║  ██║██║ ██║██╔═██╗██║    ██╔══╝  ║', Colors.GREEN))
    print(color('║ ██████║╚█████╔╝╚████╔╝██║ ██║╚█████╗██████╗ ║', Colors.GREEN))
    print(color('║ ╚═════╝ ╚════╝  ╚═══╝ ╚═╝ ╚═╝ ╚════╝╚═════╝ ║', Colors.GREEN))
    print(color('╚═════════ configure git preferences ═════════╝', Colors.GREEN))
    print()
    print()
#!<

#!> Environment settings header
def print_env_section() -> None:
    print()
    print(color('╔══════════════════════════════════════════════════════╗', Colors.GREEN))
    print(color('║ ██████╗██╗  ██╗██╗ ██╗██████╗█████╗  █████╗ ██╗  ██╗ ║', Colors.GREEN))
    print(color('║ ██╔═══╝███╗ ██║██║ ██║╚═██╔═╝██╔═██╗██╔══██╗███╗ ██║ ║', Colors.GREEN))
    print(color('║ █████╗ ████╗██║██║ ██║  ██║  █████╔╝██║  ██║████╗██║ ║', Colors.GREEN))
    print(color('║ ██╔══╝ ██╔████║╚████╔╝  ██║  ██╔═██╗██║  ██║██╔████║ ║', Colors.GREEN))
    print(color('║ ██████╗██║╚███║ ╚██╔╝ ██████╗██║ ██║╚█████╔╝██║╚███║ ║', Colors.GREEN))
    print(color('║ ╚═════╝╚═╝ ╚══╝  ╚═╝  ╚═════╝╚═╝ ╚═╝ ╚════╝ ╚═╝ ╚══╝ ║', Colors.GREEN))
    print(color('╚════════════ configure your environment ══════════════╝', Colors.GREEN))
    print()
    print()
#!<

#!> Tool blocking
def print_blocking_header() -> None:
    print()
    print(color('╔══════════════════════════════════════════════════════════════╗', Colors.GREEN))
    print(color('║ █████╗ ██╗      █████╗  █████╗██╗  ██╗██████╗██╗  ██╗ █████╗ ║', Colors.GREEN))
    print(color('║ ██╔═██╗██║     ██╔══██╗██╔═══╝██║ ██╔╝╚═██╔═╝███╗ ██║██╔═══╝ ║', Colors.GREEN))
    print(color('║ █████╔╝██║     ██║  ██║██║    █████╔╝   ██║  ████╗██║██║     ║', Colors.GREEN))
    print(color('║ ██╔═██╗██║     ██║  ██║██║    ██╔═██╗   ██║  ██╔████║██║ ██╗ ║', Colors.GREEN))
    print(color('║ █████╔╝███████╗╚█████╔╝╚█████╗██║  ██╗██████╗██║╚███║╚█████║ ║', Colors.GREEN))
    print(color('║ ╚════╝ ╚══════╝ ╚════╝  ╚════╝╚═╝  ╚═╝╚═════╝╚═╝ ╚══╝ ╚════╝ ║', Colors.GREEN))
    print(color('╚══════════════ blocked tools and bash commands ═══════════════╝', Colors.GREEN))
    print()
    print()
#!<

#!> Read only commands section
def print_read_only_section() -> None:
    print()
    print(color('╔═══════════════════════════════════════════════════════════════════╗', Colors.GREEN))
    print(color('║ █████╗ ██████╗ █████╗ █████╗       ██╗     ██████╗██╗  ██╗██████╗ ║', Colors.GREEN))
    print(color('║ ██╔═██╗██╔═══╝██╔══██╗██╔═██╗      ██║     ╚═██╔═╝██║ ██╔╝██╔═══╝ ║', Colors.GREEN))
    print(color('║ █████╔╝█████╗ ███████║██║ ██║█████╗██║       ██║  █████╔╝ █████╗  ║', Colors.GREEN))
    print(color('║ ██╔═██╗██╔══╝ ██╔══██║██║ ██║╚════╝██║       ██║  ██╔═██╗ ██╔══╝  ║', Colors.GREEN))
    print(color('║ ██║ ██║██████╗██║  ██║█████╔╝      ███████╗██████╗██║  ██╗██████╗ ║', Colors.GREEN))
    print(color('║ ╚═╝ ╚═╝╚═════╝╚═╝  ╚═╝╚════╝       ╚══════╝╚═════╝╚═╝  ╚═╝╚═════╝ ║', Colors.GREEN))
    print(color('╚═══════════════ bash commands claude can use freely ═══════════════╝', Colors.GREEN))
    print()
    print()
#!<

#!> Write-like commands section
def print_write_like_section() -> None:
    print()
    print(color("╔════════════════════════════════════════════════════════════════════════════╗",Colors.GREEN))
    print(color("║ ██╗    ██╗█████╗ ██████╗██████╗██████╗      ██╗     ██████╗██╗  ██╗██████╗ ║",Colors.GREEN))
    print(color("║ ██║    ██║██╔═██╗╚═██╔═╝╚═██╔═╝██╔═══╝      ██║     ╚═██╔═╝██║ ██╔╝██╔═══╝ ║",Colors.GREEN))
    print(color("║ ██║ █╗ ██║█████╔╝  ██║    ██║  █████╗ █████╗██║       ██║  █████╔╝ █████╗  ║",Colors.GREEN))
    print(color("║ ██║███╗██║██╔═██╗  ██║    ██║  ██╔══╝ ╚════╝██║       ██║  ██╔═██╗ ██╔══╝  ║",Colors.GREEN))
    print(color("║ ╚███╔███╔╝██║ ██║██████╗  ██║  ██████╗      ███████╗██████╗██║  ██╗██████╗ ║",Colors.GREEN))
    print(color("║  ╚══╝╚══╝ ╚═╝ ╚═╝╚═════╝  ╚═╝  ╚═════╝      ╚══════╝╚═════╝╚═╝  ╚═╝╚═════╝ ║",Colors.GREEN))
    print(color("╚═══════════════ commands claude can't use in discussion mode ═══════════════╝",Colors.GREEN))
    print()
    print()
#!<

#!> Extrasafe section
def print_extrasafe_section() -> None:
    print()
    print(color("╔════════════════════════════════════════════════════════════════════╗",Colors.GREEN))
    print(color("║ ██████╗██╗  ██╗██████╗█████╗  █████╗ ██████╗ █████╗ ██████╗██████╗ ║",Colors.GREEN))
    print(color("║ ██╔═══╝╚██╗██╔╝╚═██╔═╝██╔═██╗██╔══██╗██╔═══╝██╔══██╗██╔═══╝██╔═══╝ ║",Colors.GREEN))
    print(color("║ █████╗  ╚███╔╝   ██║  █████╔╝███████║██████╗███████║█████╗ █████╗  ║",Colors.GREEN))
    print(color("║ ██╔══╝  ██╔██╗   ██║  ██╔═██╗██╔══██║╚═══██║██╔══██║██╔══╝ ██╔══╝  ║",Colors.GREEN))
    print(color("║ ██████╗██╔╝ ██╗  ██║  ██║ ██║██║  ██║██████║██║  ██║██║    ██████╗ ║",Colors.GREEN))
    print(color("║ ╚═════╝╚═╝  ╚═╝  ╚═╝  ╚═╝ ╚═╝╚═╝  ╚═╝╚═════╝╚═╝  ╚═╝╚═╝    ╚═════╝ ║",Colors.GREEN))
    print(color("╚════════════ toggle blocking for unrecognized commands ═════════════╝",Colors.GREEN))
    print()
    print()
#!<

#!> Trigger phrases
def print_triggers_header() -> None:
    print()
    print(color('╔══════════════════════════════════════════════════════════╗',Colors.GREEN))
    print(color('║ ██████╗█████╗ ██████╗ █████╗ █████╗██████╗█████╗ ██████╗ ║',Colors.GREEN))
    print(color('║ ╚═██╔═╝██╔═██╗╚═██╔═╝██╔═══╝██╔═══╝██╔═══╝██╔═██╗██╔═══╝ ║',Colors.GREEN))
    print(color('║   ██║  █████╔╝  ██║  ██║    ██║    █████╗ █████╔╝██████╗ ║',Colors.GREEN))
    print(color('║   ██║  ██╔═██╗  ██║  ██║ ██╗██║ ██╗██╔══╝ ██╔═██╗╚═══██║ ║',Colors.GREEN))
    print(color('║   ██║  ██║ ██║██████╗╚█████║╚█████║██████╗██║ ██║██████║ ║',Colors.GREEN))
    print(color('║   ╚═╝  ╚═╝ ╚═╝╚═════╝ ╚════╝ ╚════╝╚═════╝╚═╝ ╚═╝╚═════╝ ║',Colors.GREEN))
    print(color('╚════════ natural language controls for Claude Code ═══════╝',Colors.GREEN))
    print()
    print()
#!<

#!> Implementation mode triggers section
def print_go_triggers_section() -> None:
    print()
    print(color('╔══════════════════════════════════════════════════════════════════════════╗',Colors.GREEN))
    print(color('║ ██████╗███╗  ███╗██████╗ ██╗     ██████╗███╗  ███╗██████╗██╗  ██╗██████╗ ║',Colors.GREEN))
    print(color('║ ╚═██╔═╝████╗████║██╔══██╗██║     ██╔═══╝████╗████║██╔═══╝███╗ ██║╚═██╔═╝ ║',Colors.GREEN))
    print(color('║   ██║  ██╔███║██║██████╔╝██║     █████╗ ██╔███║██║█████╗ ████╗██║  ██║   ║',Colors.GREEN))
    print(color('║   ██║  ██║╚══╝██║██╔═══╝ ██║     ██╔══╝ ██║╚══╝██║██╔══╝ ██╔████║  ██║   ║',Colors.GREEN))
    print(color('║ ██████╗██║    ██║██║     ███████╗██████╗██║    ██║██████╗██║╚███║  ██║   ║',Colors.GREEN))
    print(color('║ ╚═════╝╚═╝    ╚═╝╚═╝     ╚══════╝╚═════╝╚═╝    ╚═╝╚═════╝╚═╝ ╚══╝  ╚═╝   ║',Colors.GREEN))
    print(color('╚════════════ activate implementation mode (claude can code) ══════════════╝',Colors.GREEN))
    print()
    print()
#!<

#!> Discussion mode triggers section
def print_no_triggers_section() -> None:
    print()
    print(color('╔═══════════════════════════════════════════════════╗',Colors.GREEN))
    print(color('║ █████╗ ██████╗██████╗ █████╗██╗ ██╗██████╗██████╗ ║',Colors.GREEN))
    print(color('║ ██╔═██╗╚═██╔═╝██╔═══╝██╔═══╝██║ ██║██╔═══╝██╔═══╝ ║',Colors.GREEN))
    print(color('║ ██║ ██║  ██║  ██████╗██║    ██║ ██║██████╗██████╗ ║',Colors.GREEN))
    print(color('║ ██║ ██║  ██║  ╚═══██║██║    ██║ ██║╚═══██║╚═══██║ ║',Colors.GREEN))
    print(color('║ █████╔╝██████╗██████║╚█████╗╚████╔╝██████║██████║ ║',Colors.GREEN))
    print(color('║ ╚════╝ ╚═════╝╚═════╝ ╚════╝ ╚═══╝ ╚═════╝╚═════╝ ║',Colors.GREEN))
    print(color('╚════════════ activate discussion mode ════════════╝',Colors.GREEN))
    print()
    print()
#!<

#!> Create triggers section
def print_create_section() -> None:
    print()
    print(color('╔═════════════════════════════════════════════╗',Colors.GREEN))
    print(color('║  █████╗█████╗ ██████╗ █████╗ ██████╗██████╗ ║',Colors.GREEN))
    print(color('║ ██╔═══╝██╔═██╗██╔═══╝██╔══██╗╚═██╔═╝██╔═══╝ ║',Colors.GREEN))
    print(color('║ ██║    █████╔╝█████╗ ███████║  ██║  █████╗  ║',Colors.GREEN))
    print(color('║ ██║    ██╔═██╗██╔══╝ ██╔══██║  ██║  ██╔══╝  ║',Colors.GREEN))
    print(color('║ ╚█████╗██║ ██║██████╗██║  ██║  ██║  ██████╗ ║',Colors.GREEN))
    print(color('║  ╚════╝╚═╝ ╚═╝╚═════╝╚═╝  ╚═╝  ╚═╝  ╚═════╝ ║',Colors.GREEN))
    print(color('╚══════ activate task creation protocol ══════╝',Colors.GREEN))
    print()
    print()
#!<

#!> Startup triggers section
def print_startup_section() -> None:
    print()
    print(color('╔═════════════════════════════════════════════════════╗',Colors.GREEN))
    print(color('║ ██████╗██████╗ █████╗ █████╗ ██████╗██╗ ██╗██████╗  ║',Colors.GREEN))
    print(color('║ ██╔═══╝╚═██╔═╝██╔══██╗██╔═██╗╚═██╔═╝██║ ██║██╔══██╗ ║',Colors.GREEN))
    print(color('║ ██████╗  ██║  ███████║█████╔╝  ██║  ██║ ██║██████╔╝ ║',Colors.GREEN))
    print(color('║ ╚═══██║  ██║  ██╔══██║██╔═██╗  ██║  ██║ ██║██╔═══╝  ║',Colors.GREEN))
    print(color('║ ██████║  ██║  ██║  ██║██║ ██║  ██║  ╚████╔╝██║      ║',Colors.GREEN))
    print(color('║ ╚═════╝  ╚═╝  ╚═╝  ╚═╝╚═╝ ╚═╝  ╚═╝   ╚═══╝ ╚═╝      ║',Colors.GREEN))
    print(color('╚══════════ activate task startup protocol ═══════════╝',Colors.GREEN))
    print()
    print()
#!<

#!> Completion triggers section
def print_complete_section() -> None:
    print()
    print(color('╔════════════════════════════════════════════════════════════════╗',Colors.GREEN))
    print(color('║  █████╗ █████╗ ███╗  ███╗██████╗ ██╗     ██████╗██████╗██████╗ ║',Colors.GREEN))
    print(color('║ ██╔═══╝██╔══██╗████╗████║██╔══██╗██║     ██╔═══╝╚═██╔═╝██╔═══╝ ║',Colors.GREEN))
    print(color('║ ██║    ██║  ██║██╔███║██║██████╔╝██║     █████╗   ██║  █████╗  ║',Colors.GREEN))
    print(color('║ ██║    ██║  ██║██║╚══╝██║██╔═══╝ ██║     ██╔══╝   ██║  ██╔══╝  ║',Colors.GREEN))
    print(color('║ ╚█████╗╚█████╔╝██║    ██║██║     ███████╗██████╗  ██║  ██████╗ ║',Colors.GREEN))
    print(color('║  ╚════╝ ╚════╝ ╚═╝    ╚═╝╚═╝     ╚══════╝╚═════╝  ╚═╝  ╚═════╝ ║',Colors.GREEN))
    print(color('╚══════════════ activate task completion protocol ═══════════════╝',Colors.GREEN))
    print()
    print()
#!<

#!> Compaction triggers section
def print_compact_section() -> None:
    print()
    print(color('╔═════════════════════════════════════════════════════════╗',Colors.GREEN))
    print(color('║  █████╗ █████╗ ███╗  ███╗██████╗  █████╗  █████╗██████╗ ║',Colors.GREEN))
    print(color('║ ██╔═══╝██╔══██╗████╗████║██╔══██╗██╔══██╗██╔═══╝╚═██╔═╝ ║',Colors.GREEN))
    print(color('║ ██║    ██║  ██║██╔███║██║██████╔╝███████║██║      ██║   ║',Colors.GREEN))
    print(color('║ ██║    ██║  ██║██║╚══╝██║██╔═══╝ ██╔══██║██║      ██║   ║',Colors.GREEN))
    print(color('║ ╚█████╗╚█████╔╝██║    ██║██║     ██║  ██║╚█████╗  ██║   ║',Colors.GREEN))
    print(color('║  ╚════╝ ╚════╝ ╚═╝    ╚═╝╚═╝     ╚═╝  ╚═╝ ╚════╝  ╚═╝   ║',Colors.GREEN))
    print(color('╚═════════ activate context compaction protocol ══════════╝',Colors.GREEN))
    print()
    print()
#!<

#!> Feature toggles header
def print_features_header() -> None:
    print()
    print(color('╔═══════════════════════════════════════════════════════════╗',Colors.GREEN))
    print(color('║ ██████╗██████╗ █████╗ ██████╗██╗ ██╗█████╗ ██████╗██████╗ ║',Colors.GREEN))
    print(color('║ ██╔═══╝██╔═══╝██╔══██╗╚═██╔═╝██║ ██║██╔═██╗██╔═══╝██╔═══╝ ║',Colors.GREEN))
    print(color('║ █████╗ █████╗ ███████║  ██║  ██║ ██║█████╔╝█████╗ ██████╗ ║',Colors.GREEN))
    print(color('║ ██╔══╝ ██╔══╝ ██╔══██║  ██║  ██║ ██║██╔═██╗██╔══╝ ╚═══██║ ║',Colors.GREEN))
    print(color('║ ██║    ██████╗██║  ██║  ██║  ╚████╔╝██║ ██║██████╗██████║ ║',Colors.GREEN))
    print(color('║ ╚═╝    ╚═════╝╚═╝  ╚═╝  ╚═╝   ╚═══╝ ╚═╝ ╚═╝╚═════╝╚═════╝ ║',Colors.GREEN))
    print(color('╚════════════ turn on/off cc-sessions features ═════════════╝',Colors.GREEN))
    print()
    print()
#!<

#!> Statusline header
def print_statusline_header() -> None:
    print()
    print(color('╔═══════════════════════════════════════════════════════════════════════════╗',Colors.GREEN))
    print(color('║ ██████╗██████╗ █████╗ ██████╗██╗ ██╗██████╗██╗     ██████╗██╗  ██╗██████╗ ║',Colors.GREEN))
    print(color('║ ██╔═══╝╚═██╔═╝██╔══██╗╚═██╔═╝██║ ██║██╔═══╝██║     ╚═██╔═╝███╗ ██║██╔═══╝ ║',Colors.GREEN))
    print(color('║ ██████╗  ██║  ███████║  ██║  ██║ ██║██████╗██║       ██║  ████╗██║█████╗  ║',Colors.GREEN))
    print(color('║ ╚═══██║  ██║  ██╔══██║  ██║  ██║ ██║╚═══██║██║       ██║  ██╔████║██╔══╝  ║',Colors.GREEN))
    print(color('║ ██████║  ██║  ██║  ██║  ██║  ╚████╔╝██████║███████╗██████╗██║╚███║██████╗ ║',Colors.GREEN))
    print(color('║ ╚═════╝  ╚═╝  ╚═╝  ╚═╝  ╚═╝   ╚═══╝ ╚═════╝╚══════╝╚═════╝╚═╝ ╚══╝╚═════╝ ║',Colors.GREEN))
    print(color('╚═════════════ cc-sessions custom statusline w/ modes + tasks ══════════════╝',Colors.GREEN))
    print()
    print()
#!<

#!> Kickstart header
def print_kickstart_header() -> None:
    print()
    print(color('╔════════════════════════════════════════════════════════════════════╗',Colors.GREEN))
    print(color('║ ██╗  ██╗██████╗ █████╗██╗  ██╗██████╗██████╗ █████╗ █████╗ ██████╗ ║',Colors.GREEN))
    print(color('║ ██║ ██╔╝╚═██╔═╝██╔═══╝██║ ██╔╝██╔═══╝╚═██╔═╝██╔══██╗██╔═██╗╚═██╔═╝ ║',Colors.GREEN))
    print(color('║ █████╔╝   ██║  ██║    █████╔╝ ██████╗  ██║  ███████║█████╔╝  ██║   ║',Colors.GREEN))
    print(color('║ ██╔═██╗   ██║  ██║    ██╔═██╗ ╚═══██║  ██║  ██╔══██║██╔═██╗  ██║   ║',Colors.GREEN))
    print(color('║ ██║  ██╗██████╗╚█████╗██║  ██╗██████║  ██║  ██║  ██║██║ ██║  ██║   ║',Colors.GREEN))
    print(color('║ ╚═╝  ╚═╝╚═════╝ ╚════╝╚═╝  ╚═╝╚═════╝  ╚═╝  ╚═╝  ╚═╝╚═╝ ╚═╝  ╚═╝   ║',Colors.GREEN))
    print(color('╚════════════════════════════════════════════════════════════════════╝',Colors.GREEN))
    print()
    print()


#!<

##-##

## ===== FILESYSTEM ===== ##

#!> Previous install - create backup
def create_backup(project_root):
    """Create timestamped backup of tasks and agents before reinstall."""
    from datetime import datetime

    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    backup_dir = project_root / '.claude' / f'.backup-{timestamp}'

    print(color(f'\n💾 Creating backup at {backup_dir.relative_to(project_root)}/...', Colors.CYAN))

    backup_dir.mkdir(parents=True, exist_ok=True)

    # Backup all task files (includes done/, indexes/, and all task files)
    tasks_src = project_root / 'sessions' / 'tasks'
    task_count = 0
    if tasks_src.exists():
        tasks_dest = backup_dir / 'tasks'
        copy_directory(tasks_src, tasks_dest)

        # Count task files for user feedback and verification
        task_count = sum(1 for f in tasks_src.rglob('*.md'))
        backed_up_count = sum(1 for f in tasks_dest.rglob('*.md'))

        if task_count != backed_up_count:
            print(color(f'   ✗ Backup verification failed: {backed_up_count}/{task_count} files backed up', Colors.RED))
            raise Exception('Backup verification failed - aborting to prevent data loss')

        print(color(f'   ✓ Backed up {task_count} task files', Colors.GREEN))

    # Backup all agents
    agents_src = project_root / '.claude' / 'agents'
    if agents_src.exists():
        script_agents = get_package_root() / 'agents'
        agents_dest = backup_dir / 'agents'
        to_backup: list[tuple[Path, Path]] = []
        for p in agents_src.rglob('*'):
            if not p.is_file():
                continue
            rel = p.relative_to(agents_src)
            src_pkg = script_agents / rel
            # Only back up if we are installing a same-named file and contents differ
            if src_pkg.exists() and _files_differ(src_pkg, p):
                to_backup.append((p, agents_dest / rel))
        # Perform backup copies
        for src_file, dst_file in to_backup:
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dst_file)
        # Verify
        backed_up_agents = sum(1 for _ in agents_dest.rglob('*') if _.is_file()) if agents_dest.exists() else 0
        if backed_up_agents != len(to_backup):
            print(color(f'   ✗ Backup verification failed: {backed_up_agents}/{len(to_backup)} modified agents backed up', Colors.RED))
            raise Exception('Backup verification failed - aborting to prevent data loss')
        print(color(f'   ✓ Backed up {len(to_backup)} modified agent file(s)', Colors.GREEN))

    return backup_dir
#!<

#!> Create directory structure
def create_directory_structure(project_root):
    print(color('Creating directory structure...', Colors.CYAN))

    dirs = [
        '.claude',
        '.claude/agents',
        '.claude/commands',
        'sessions',
        'sessions/tasks',
        'sessions/tasks/done',
        'sessions/tasks/indexes',
        'sessions/hooks',
        'sessions/api',
        'sessions/protocols',
        'sessions/knowledge',
        'sessions/learnings',
        'sessions/learnings/topics'
    ]

    for dir_name in dirs:
        full_path = project_root / dir_name
        full_path.mkdir(parents=True, exist_ok=True)
#!<

#!> Copy files
def copy_files(script_dir, project_root):
    print(color('Installing files...', Colors.CYAN))

    # Copy agents
    agents_source = script_dir / 'agents'
    agents_dest = project_root / '.claude' / 'agents'
    if agents_source.exists():
        copied, skipped = copy_agents_if_changed(agents_source, agents_dest)
        if copied:
            print(color(f'   ✓ Installed/updated {copied} agent file(s)', Colors.GREEN))
        if skipped:
            print(color(f'   • Skipped {skipped} identical agent file(s)', Colors.GRAY))

    # Copy knowledge base
    knowledge_source = script_dir / 'knowledge'
    knowledge_dest = project_root / 'sessions' / 'knowledge'
    if knowledge_source.exists():
        copy_directory(knowledge_source, knowledge_dest)

    print(color('Installing Python-specific files...', Colors.CYAN))

    py_root = script_dir / 'python'

    # Copy statusline
    copy_file(py_root / 'statusline.py', project_root / 'sessions' / 'statusline.py')

    # Copy API
    copy_directory(py_root / 'api', project_root / 'sessions' / 'api')

    # Copy bin (wrapper scripts for sessions command)
    copy_directory(py_root / 'bin', project_root / 'sessions' / 'bin')

    # Copy hooks
    copy_directory(py_root / 'hooks', project_root / 'sessions' / 'hooks')

    # Copy protocols from shared directory
    copy_directory(script_dir / 'protocols', project_root / 'sessions' / 'protocols')

    # Copy commands from shared directory
    copy_directory(script_dir / 'commands', project_root / '.claude' / 'commands')

    # Copy templates from shared directory to their respective destinations
    templates_dir = script_dir / 'templates'

    copy_file(templates_dir / 'CLAUDE.sessions.md', project_root / 'sessions' / 'CLAUDE.sessions.md')

    copy_file(templates_dir / 'TEMPLATE.md', project_root / 'sessions' / 'tasks' / 'TEMPLATE.md')

    copy_file(templates_dir / 'h-kickstart-setup.md', project_root / 'sessions' / 'tasks' / 'h-kickstart-setup.md')

    copy_file(templates_dir / 'INDEX_TEMPLATE.md', project_root / 'sessions' / 'tasks' / 'indexes' / 'INDEX_TEMPLATE.md')
#!<

#!> v0.2.6/v0.2.7 Migration Functions
# Detection patterns for v0.2.6 and v0.2.7 installations (identical versions)
V026_PATTERNS = {
    'version': '0.2.6',

    'hooks': {
        # Python hooks in .claude/hooks/ with hyphenated names
        'sessions-enforce.py': {
            'imports': [
                'from shared_state import check_daic_mode_bool',
                'from shared_state import get_task_state',
                'from shared_state import get_project_root',
            ],
            'unique_patterns': [
                'def load_config():',
                'DEFAULT_CONFIG = {',
                'CONFIG_FILE = PROJECT_ROOT / "sessions" / "sessions-config.json"',
            ]
        },
        'session-start.py': {
            'imports': [
                'from shared_state import get_project_root',
                'from shared_state import ensure_state_dir',
                'from shared_state import get_task_state',
            ],
            'unique_patterns': [
                'developer_name = config.get(\'developer_name\', \'the developer\')',
                'You are beginning a new context window',
                'quick_checks = []',
            ]
        },
        'user-messages.py': {
            'imports': [
                'from shared_state import check_daic_mode_bool',
                'from shared_state import set_daic_mode',
            ],
            'unique_patterns': [
                'DEFAULT_TRIGGER_PHRASES = ["make it so", "run that", "yert"]',
                'is_add_trigger_command = prompt.strip().startswith(\'/add-trigger\')',
                'get_context_length_from_transcript',
            ]
        },
        'post-tool-use.py': {
            'imports': [
                'from shared_state import check_daic_mode_bool',
                'from shared_state import get_project_root',
            ],
            'unique_patterns': [
                'subagent_flag = project_root / \'.claude\' / \'state\' / \'in_subagent_context.flag\'',
                '[DAIC Reminder] When you\'re done implementing, run: daic',
                'implementation_tools = ["Edit", "Write", "MultiEdit", "NotebookEdit"]',
            ]
        },
        'task-transcript-link.py': {
            'imports': [
                'import tiktoken',
                'import json',
            ],
            'unique_patterns': [
                'tool_name = input_data.get("tool_name", "")',
                'if tool_name != "Task":',
                'Clean the transcript',
            ]
        },
        'shared_state.py': {
            'imports': [
                'import json',
                'from pathlib import Path',
                'from datetime import datetime',
            ],
            'unique_patterns': [
                'def get_project_root():',
                'STATE_DIR = PROJECT_ROOT / ".claude" / "state"',
                'DAIC_STATE_FILE = STATE_DIR / "daic-mode.json"',
                'TASK_STATE_FILE = STATE_DIR / "current_task.json"',
                'DISCUSSION_MODE_MSG = "You are now in Discussion Mode',
                'def check_daic_mode_bool() -> bool:',
                'def toggle_daic_mode() -> str:',
            ]
        },
    },

    'state_files': {
        'daic-mode.json': {
            'location': '.claude/state/',
            'schema': {
                'type': 'object',
                'required_keys': ['mode'],
                'properties': {
                    'mode': {'enum': ['discussion', 'implementation']}
                }
            },
            'example': {'mode': 'discussion'}
        },
        'current_task.json': {
            'location': '.claude/state/',
            'schema': {
                'type': 'object',
                'required_keys': ['task', 'branch', 'services', 'updated'],
                'properties': {
                    'task': {'type': ['string', 'null']},
                    'branch': {'type': ['string', 'null']},
                    'services': {'type': 'array'},
                    'updated': {'type': 'string', 'format': 'date'}
                }
            },
            'example': {
                'task': None,
                'branch': None,
                'services': [],
                'updated': '2025-10-13'
            }
        },
        'in_subagent_context.flag': {
            'location': '.claude/state/',
            'schema': {'type': 'flag_file'},
            'note': 'Presence indicates subagent context; no content validation needed'
        }
    },

    'statusline': {
        'location': '.claude/statusline-script.sh',
        'unique_patterns': [
            '#!/bin/bash',
            '# Claude Code StatusLine Script',
            'calculate_context() {',
            'context_limit=800000',
            'if [[ "$model_name" == *"Sonnet"* ]]; then',
        ],
        'note': 'Optional installation - may not be present'
    },

    'settings_paths': {
        'unix': {
            'hooks_dir': '.claude/hooks',
            'command_pattern': '$CLAUDE_PROJECT_DIR/.claude/hooks/{hookname}.py',
            'example': '$CLAUDE_PROJECT_DIR/.claude/hooks/sessions-enforce.py'
        },
        'windows': {
            'hooks_dir': '.claude\\hooks',
            'command_pattern': 'python "%CLAUDE_PROJECT_DIR%\\.claude\\hooks\\{hookname}.py"',
            'example': 'python "%CLAUDE_PROJECT_DIR%\\.claude\\hooks\\sessions-enforce.py"'
        },
        'hook_names': [
            'user-messages',
            'sessions-enforce',
            'task-transcript-link',
            'post-tool-use',
            'session-start',
        ]
    },

    'directory_structure': {
        'directories': [
            '.claude/hooks/',
            '.claude/state/',
        ],
        'note': 'Both directories should be created by v0.2.6 installer'
    }
}

def is_v026_hook(file_path: Path) -> bool:
    """Verify if a file is a v0.2.6/v0.2.7 cc-sessions hook using content-based detection.

    Returns True if file contains v0.2.6-specific patterns (minimum 2 matches required).
    """
    if not file_path.exists():
        return False

    hook_name = file_path.name
    if hook_name not in V026_PATTERNS['hooks']:
        return False

    patterns = V026_PATTERNS['hooks'][hook_name]

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = ''.join(f.readline() for _ in range(80))

        matches = 0
        for import_pattern in patterns['imports']:
            if import_pattern in content:
                matches += 1

        for unique_pattern in patterns['unique_patterns']:
            if unique_pattern in content:
                matches += 1

        return matches >= 2

    except Exception:
        return False

def is_v026_state_file(file_path: Path, file_type: str) -> bool:
    """Validate if a state file matches v0.2.6/v0.2.7 schema.

    Args:
        file_path: Path to the state file
        file_type: One of 'daic-mode.json', 'current_task.json', 'in_subagent_context.flag'

    Returns True if file matches v0.2.6 schema.
    """
    if not file_path.exists():
        return False

    if file_type not in V026_PATTERNS['state_files']:
        return False

    # Special case: flag file, just check existence
    if file_type == 'in_subagent_context.flag':
        return True

    # Validate JSON files
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        schema = V026_PATTERNS['state_files'][file_type]['schema']
        required_keys = schema.get('required_keys', [])

        if not all(key in data for key in required_keys):
            return False

        if file_type == 'daic-mode.json':
            return data.get('mode') in ['discussion', 'implementation']

        if file_type == 'current_task.json':
            return (
                isinstance(data.get('services'), list) and
                (isinstance(data.get('task'), (str, type(None)))) and
                (isinstance(data.get('branch'), (str, type(None)))) and
                isinstance(data.get('updated'), str)
            )

        return True

    except (json.JSONDecodeError, Exception):
        return False

def find_v026_hook_commands(settings: dict) -> list:
    """Extract hook commands from settings.json that reference v0.2.6/v0.2.7 paths.

    Returns list of dicts with event, matcher, command, and hook_name fields.
    """
    v026_commands = []
    hooks = settings.get('hooks', {})

    if not isinstance(hooks, dict):
        return v026_commands

    for event_name, event_configs in hooks.items():
        if not isinstance(event_configs, list):
            continue

        for config in event_configs:
            if not isinstance(config, dict):
                continue

            hook_list = config.get('hooks', [])
            matcher = config.get('matcher')

            for hook in hook_list:
                command = hook.get('command', '')
                is_v026 = False
                hook_name = None

                # Unix pattern: $CLAUDE_PROJECT_DIR/.claude/hooks/{name}.py
                if '/.claude/hooks/' in command:
                    is_v026 = True
                    parts = command.split('/.claude/hooks/')
                    if len(parts) > 1:
                        hook_file = parts[1].split()[0]
                        hook_name = hook_file.replace('.py', '').replace('.js', '')

                # Windows pattern: %.claude\hooks\{name}.py
                elif '\\.claude\\hooks\\' in command or '\\.claude\\\\hooks\\\\' in command:
                    is_v026 = True
                    parts = command.split('\\hooks\\')
                    if len(parts) > 1:
                        hook_file = parts[1].split('"')[0]
                        hook_name = hook_file.replace('.py', '').replace('.js', '')

                # Verify known cc-sessions hook name
                if is_v026 and hook_name:
                    known_hooks = V026_PATTERNS['settings_paths']['hook_names']
                    if hook_name in known_hooks:
                        v026_commands.append({
                            'event': event_name,
                            'matcher': matcher,
                            'command': command,
                            'hook_name': hook_name
                        })

    return v026_commands

def detect_v026_artifacts(project_root: Path) -> dict:
    """Comprehensive detection of all v0.2.6/v0.2.7 artifacts.

    Returns dict with hooks, state_files, statusline, settings_commands, command_files, and directories.
    """
    artifacts = {
        'hooks': [],
        'state_files': [],
        'statusline': False,
        'settings_commands': [],
        'command_files': [],
        'directories': []
    }

    # Check hooks directory
    hooks_dir = project_root / '.claude' / 'hooks'
    if hooks_dir.exists():
        artifacts['directories'].append('.claude/hooks/')
        for hook_name in V026_PATTERNS['hooks'].keys():
            hook_path = hooks_dir / hook_name
            if is_v026_hook(hook_path):
                artifacts['hooks'].append(hook_name)

    # Check state directory
    state_dir = project_root / '.claude' / 'state'
    if state_dir.exists():
        artifacts['directories'].append('.claude/state/')

        daic_file = state_dir / 'daic-mode.json'
        if is_v026_state_file(daic_file, 'daic-mode.json'):
            artifacts['state_files'].append('daic-mode.json')

        task_file = state_dir / 'current_task.json'
        if is_v026_state_file(task_file, 'current_task.json'):
            artifacts['state_files'].append('current_task.json')

        subagent_flag = state_dir / 'in_subagent_context.flag'
        if is_v026_state_file(subagent_flag, 'in_subagent_context.flag'):
            artifacts['state_files'].append('in_subagent_context.flag')

    # Check statusline
    statusline_path = project_root / '.claude' / 'statusline-script.sh'
    if statusline_path.exists():
        try:
            with open(statusline_path, 'r', encoding='utf-8') as f:
                header = f.read(200)
                if '# Claude Code StatusLine Script' in header:
                    artifacts['statusline'] = True
        except Exception:
            pass

    # Check settings.json
    try:
        settings = get_settings(project_root)
        artifacts['settings_commands'] = find_v026_hook_commands(settings)
    except Exception:
        pass

    # Check for old command files
    commands_dir = project_root / '.claude' / 'commands'
    if commands_dir.exists():
        old_commands = ['add-trigger.md', 'api-mode.md']
        for cmd_file in old_commands:
            cmd_path = commands_dir / cmd_file
            if cmd_path.exists():
                artifacts['command_files'].append(cmd_file)

    return artifacts

def prompt_migration_confirmation(artifacts: dict) -> bool:
    """Show user what will be migrated and ask for confirmation.

    Returns True if user confirms migration, False otherwise.
    """
    show_header(print_installer_header)

    info = [
        color('🔄 v0.2.6/v0.2.7 Installation Detected', Colors.CYAN),
        '',
        color('Found the following artifacts from previous installation:', Colors.CYAN)
    ]

    if artifacts['hooks']:
        info.append(color(f'  • Hooks: {len(artifacts["hooks"])} files', Colors.CYAN))
        for hook in artifacts['hooks']:
            info.append(color(f'    - {hook}', Colors.CYAN))

    if artifacts['state_files']:
        info.append(color(f'  • State files: {len(artifacts["state_files"])} files', Colors.CYAN))
        for state_file in artifacts['state_files']:
            info.append(color(f'    - {state_file}', Colors.CYAN))

    if artifacts['statusline']:
        info.append(color('  • Statusline script: statusline-script.sh', Colors.CYAN))

    if artifacts['settings_commands']:
        info.append(color(f'  • Settings.json: {len(artifacts["settings_commands"])} hook commands', Colors.CYAN))

    if artifacts['command_files']:
        info.append(color(f'  • Command files: {len(artifacts["command_files"])} files', Colors.CYAN))
        for cmd_file in artifacts['command_files']:
            info.append(color(f'    - {cmd_file}', Colors.CYAN))

    info.append('')
    info.append(color('These old files will be removed:', Colors.CYAN))
    info.append(color('  • Old hook files deleted', Colors.CYAN))
    info.append(color('  • Old state files deleted', Colors.CYAN))
    info.append(color('  • Settings.json cleaned', Colors.CYAN))
    info.append(color('  • You will start fresh with v0.3.0 defaults', Colors.CYAN))
    info.append('')

    set_info(info)

    choice = inquirer.list_input(
        message='Proceed with migration?',
        choices=['Yes - Migrate and clean up', 'No - Skip migration (not recommended)']
    )

    return choice.startswith('Yes')


def clean_v026_settings(project_root: Path, settings: dict, commands: list) -> bool:
    """Remove v0.2.6/v0.2.7 hook commands from settings.json.

    Args:
        project_root: Project root path
        settings: Current settings dict
        commands: List of v0.2.6 commands to remove

    Returns True on success, False on failure.
    """
    if not commands:
        return True

    try:
        import copy
        modified = copy.deepcopy(settings)

        if 'hooks' not in modified:
            return True

        # Group commands by event for efficient removal
        by_event = {}
        for cmd in commands:
            event = cmd['event']
            if event not in by_event:
                by_event[event] = []
            by_event[event].append(cmd)

        # Process each event
        for event_name, event_commands in by_event.items():
            if event_name not in modified['hooks']:
                continue

            event_configs = modified['hooks'][event_name]
            new_configs = []

            for config in event_configs:
                if not isinstance(config, dict):
                    new_configs.append(config)
                    continue

                hook_list = config.get('hooks', [])
                new_hooks = []

                for hook in hook_list:
                    command = hook.get('command', '')
                    # Check if this command should be removed
                    should_remove = any(
                        cmd['command'] == command
                        for cmd in event_commands
                    )
                    if not should_remove:
                        new_hooks.append(hook)

                # Keep config if it has remaining hooks
                if new_hooks:
                    config['hooks'] = new_hooks
                    new_configs.append(config)

            # Update or remove event
            if new_configs:
                modified['hooks'][event_name] = new_configs
            else:
                del modified['hooks'][event_name]

        # Write back
        return write_settings(project_root, modified)

    except Exception as e:
        print(color(f'✗ Failed to clean settings.json: {e}', Colors.RED))
        return False

def archive_v026_files(project_root: Path, artifacts: dict) -> dict:
    """Archive v0.2.6/v0.2.7 files before deletion.

    Returns dict with archive info: {'archived': bool, 'path': str, 'file_count': int}
    """
    from datetime import datetime
    import shutil

    # Create archive directory with timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d')
    archive_root = project_root / 'sessions' / '.archived' / f'v026-migration-{timestamp}'
    archive_hooks_dir = archive_root / 'hooks'
    archive_state_dir = archive_root / 'state'
    archive_commands_dir = archive_root / 'commands'

    try:
        archive_hooks_dir.mkdir(parents=True, exist_ok=True)
        archive_state_dir.mkdir(parents=True, exist_ok=True)
        archive_commands_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(color(f'⚠️  Could not create archive directory: {e}', Colors.YELLOW))
        return {'archived': False, 'path': '', 'file_count': 0}

    file_count = 0

    # Archive hooks
    for hook_name in artifacts['hooks']:
        try:
            src = project_root / '.claude' / 'hooks' / hook_name
            dst = archive_hooks_dir / hook_name
            if src.exists():
                shutil.copy2(src, dst)
                file_count += 1
        except Exception as e:
            print(color(f'⚠️  Could not archive {hook_name}: {e}', Colors.YELLOW))

    # Archive state files
    for state_file in artifacts['state_files']:
        try:
            src = project_root / '.claude' / 'state' / state_file
            dst = archive_state_dir / state_file
            if src.exists():
                shutil.copy2(src, dst)
                file_count += 1
        except Exception as e:
            print(color(f'⚠️  Could not archive {state_file}: {e}', Colors.YELLOW))

    # Archive statusline
    if artifacts['statusline']:
        try:
            src = project_root / '.claude' / 'statusline-script.sh'
            dst = archive_root / 'statusline-script.sh'
            if src.exists():
                shutil.copy2(src, dst)
                file_count += 1
        except Exception as e:
            print(color(f'⚠️  Could not archive statusline-script.sh: {e}', Colors.YELLOW))

    # Archive command files
    for cmd_file in artifacts['command_files']:
        try:
            src = project_root / '.claude' / 'commands' / cmd_file
            dst = archive_commands_dir / cmd_file
            if src.exists():
                shutil.copy2(src, dst)
                file_count += 1
        except Exception as e:
            print(color(f'⚠️  Could not archive {cmd_file}: {e}', Colors.YELLOW))

    # Return archive info
    relative_path = archive_root.relative_to(project_root)
    return {
        'archived': file_count > 0,
        'path': str(relative_path),
        'file_count': file_count
    }

def clean_v026_files(project_root: Path, artifacts: dict) -> None:
    """Delete verified v0.2.6/v0.2.7 files after successful migration."""
    print(color('\n🗑️  Cleaning up old files...', Colors.CYAN))

    # Remove hooks
    for hook_name in artifacts['hooks']:
        try:
            hook_path = project_root / '.claude' / 'hooks' / hook_name
            hook_path.unlink()
            print(color(f'  ✓ Removed {hook_name}', Colors.CYAN))
        except Exception as e:
            print(color(f'  ⚠ Could not remove {hook_name}: {e}', Colors.YELLOW))

    # Remove state files
    for state_file in artifacts['state_files']:
        try:
            state_path = project_root / '.claude' / 'state' / state_file
            state_path.unlink()
            print(color(f'  ✓ Removed {state_file}', Colors.CYAN))
        except Exception as e:
            print(color(f'  ⚠ Could not remove {state_file}: {e}', Colors.YELLOW))

    # Remove statusline
    if artifacts['statusline']:
        try:
            statusline_path = project_root / '.claude' / 'statusline-script.sh'
            statusline_path.unlink()
            print(color('  ✓ Removed statusline-script.sh', Colors.CYAN))
        except Exception as e:
            print(color(f'  ⚠ Could not remove statusline: {e}', Colors.YELLOW))

    # Remove command files
    for cmd_file in artifacts['command_files']:
        try:
            cmd_path = project_root / '.claude' / 'commands' / cmd_file
            cmd_path.unlink()
            print(color(f'  ✓ Removed {cmd_file}', Colors.CYAN))
        except Exception as e:
            print(color(f'  ⚠ Could not remove {cmd_file}: {e}', Colors.YELLOW))

    # Try to remove empty .claude/state/ directory (silent)
    try:
        (project_root / '.claude' / 'state').rmdir()
    except:
        pass

def run_v026_migration(project_root: Path) -> dict:
    """Orchestrate v0.2.6/v0.2.7 migration process.

    Returns dict with archive info: {'archived': bool, 'path': str, 'file_count': int, 'detected': bool}
    """
    # Detect old artifacts
    artifacts = detect_v026_artifacts(project_root)

    # Skip if no artifacts found
    if not artifacts['hooks'] and not artifacts['state_files']:
        return {'archived': False, 'path': '', 'file_count': 0, 'detected': False}

    # Prompt user
    if not prompt_migration_confirmation(artifacts):
        print(color('⚠️  Skipping cleanup. Old artifacts will remain.', Colors.YELLOW))
        print(color('   You may experience hook conflicts or unexpected behavior.', Colors.YELLOW))
        return {'archived': False, 'path': '', 'file_count': 0, 'detected': True}

    # Archive files before cleanup
    print(color('\n📁 Archiving old files...', Colors.CYAN))
    archive_info = archive_v026_files(project_root, artifacts)
    if archive_info['archived']:
        print(color(f'  ✓ Archived {archive_info["file_count"]} files to {archive_info["path"]}', Colors.CYAN))

    # Clean settings.json
    print(color('\n⚙️  Updating settings.json...', Colors.CYAN))
    settings = get_settings(project_root)
    if clean_v026_settings(project_root, settings, artifacts['settings_commands']):
        print(color(f'  ✓ Removed {len(artifacts["settings_commands"])} old hook commands', Colors.CYAN))
    else:
        print(color('  ⚠ Could not update settings.json completely', Colors.YELLOW))

    # Clean files
    clean_v026_files(project_root, artifacts)

    # Add detected flag and return archive info
    archive_info['detected'] = True
    return archive_info
#!<

#!> Configure settings.json
def write_settings(project_root: Path, settings: dict) -> bool:
    """Persist settings.json with pretty formatting using atomic write.
    Returns True on success.
    """
    try:
        settings_path = project_root / '.claude' / 'settings.json'
        settings_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to temporary file first
        next_path = settings_path.with_suffix('.json.next')
        with open(next_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)

        # Atomic rename (only reached if write succeeded)
        next_path.replace(settings_path)
        return True
    except Exception as e:
        print(color(f'✗ Failed writing settings.json: {e}', Colors.RED))
        return False

def get_settings(project_root: Path) -> dict:
    """Load settings.json, returning an empty dict if missing or invalid."""
    settings_path = project_root / '.claude' / 'settings.json'
    settings: dict = {}
    if settings_path.exists():
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        except json.JSONDecodeError:
            print(color('⚠️  Could not parse existing settings.json, will create new one', Colors.YELLOW))
        except Exception as e:
            print(color(f'⚠️  Error reading settings.json: {e}', Colors.YELLOW))
    return settings

def configure_settings(project_root: Path):
    print(color('Configuring Claude Code hooks...', Colors.CYAN))

    settings = get_settings(project_root)

    # Define sessions hooks
    is_windows = sys.platform == 'win32'
    sessions_hooks = {
        'UserPromptSubmit': [
            {
                'hooks': [
                    {
                        'type': 'command',
                        'command': 'python "%CLAUDE_PROJECT_DIR%\\sessions\\hooks\\user_messages.py"' if is_windows
                                 else 'python $CLAUDE_PROJECT_DIR/sessions/hooks/user_messages.py'
                    }
                ]
            }
        ],
        'PreToolUse': [
            {
                'matcher': 'Write|Edit|MultiEdit|Task|Bash|TodoWrite|NotebookEdit',
                'hooks': [
                    {
                        'type': 'command',
                        'command': 'python "%CLAUDE_PROJECT_DIR%\\sessions\\hooks\\sessions_enforce.py"' if is_windows
                                 else 'python $CLAUDE_PROJECT_DIR/sessions/hooks/sessions_enforce.py'
                    }
                ]
            },
            {
                'matcher': 'Task',
                'hooks': [
                    {
                        'type': 'command',
                        'command': 'python "%CLAUDE_PROJECT_DIR%\\sessions\\hooks\\subagent_hooks.py"' if is_windows
                                 else 'python $CLAUDE_PROJECT_DIR/sessions/hooks/subagent_hooks.py'
                    }
                ]
            }
        ],
        'PostToolUse': [
            {
                'hooks': [
                    {
                        'type': 'command',
                        'command': 'python "%CLAUDE_PROJECT_DIR%\\sessions\\hooks\\post_tool_use.py"' if is_windows
                                 else 'python $CLAUDE_PROJECT_DIR/sessions/hooks/post_tool_use.py'
                    }
                ]
            }
        ],
        'SessionStart': [
            {
                'matcher': 'startup|clear',
                'hooks': [
                    {
                        'type': 'command',
                        'command': 'python "%CLAUDE_PROJECT_DIR%\\sessions\\hooks\\kickstart_session_start.py"' if is_windows
                                 else 'python $CLAUDE_PROJECT_DIR/sessions/hooks/kickstart_session_start.py'
                    }
                ]
            }
        ]
    }

    # Initialize hooks object if it doesn't exist
    if 'hooks' not in settings or not isinstance(settings['hooks'], dict):
        settings['hooks'] = {}

    def find_hook_in_settings(hook_type: str, hook_block: dict) -> bool:
        """Return True if any command in hook_block already exists under hook_type."""
        for existing_cfg in settings['hooks'].get(hook_type, []) or []:
            for existing_hook in existing_cfg.get('hooks', []) or []:
                existing_cmd = existing_hook.get('command', '')
                for candidate in hook_block.get('hooks', []) or []:
                    cand_cmd = candidate.get('command', '')
                    if cand_cmd and cand_cmd in existing_cmd:
                        return True
        return False

    for hook_type, hook_blocks in sessions_hooks.items():
        # Ensure list exists
        settings['hooks'].setdefault(hook_type, [])
        # Prepend required blocks if missing (avoid duplicates)
        for block in hook_blocks:
            if not find_hook_in_settings(hook_type, block):
                settings['hooks'][hook_type] = [block] + settings['hooks'][hook_type]

    # Write updated settings
    write_settings(project_root, settings)
#!<

#!> Configure CLAUDE.md
def configure_claude_md(project_root):
    print(color('Configuring CLAUDE.md...', Colors.CYAN))

    claude_path = project_root / 'CLAUDE.md'
    reference = '@sessions/CLAUDE.sessions.md'

    if claude_path.exists():
        content = claude_path.read_text(encoding='utf-8')

        # Only add if not already present
        if reference not in content:
            # Add at the beginning after any frontmatter
            lines = content.split('\n')
            insert_index = 0

            # Skip frontmatter if it exists
            if lines[0] == '---':
                for i in range(1, len(lines)):
                    if lines[i] == '---':
                        insert_index = i + 1
                        break

            lines.insert(insert_index, '')
            lines.insert(insert_index + 1, reference)
            lines.insert(insert_index + 2, '')
            content = '\n'.join(lines)
            claude_path.write_text(content, encoding='utf-8')
    else:
        # Create minimal CLAUDE.md with reference
        minimal_claude = f"""# Additional Guidance

{reference}

This file provides instructions for Claude Code for working in the cc-sessions framework.
"""
        claude_path.write_text(minimal_claude, encoding='utf-8')
#!<

#!> Configure .gitignore
def configure_gitignore(project_root):
    print(color('Configuring .gitignore...', Colors.CYAN))

    gitignore_path = project_root / '.gitignore'
    gitignore_entries = [
        '',
        '# cc-sessions runtime files',
        'sessions/sessions-state.json',
        'sessions/transcripts/',
        'sessions/.archived/',
        ''
    ]

    if gitignore_path.exists():
        content = gitignore_path.read_text(encoding='utf-8')

        # Only add if not already present
        if 'sessions/sessions-state.json' not in content:
            # Append to end of file
            content += '\n'.join(gitignore_entries)
            gitignore_path.write_text(content, encoding='utf-8')
    else:
        # Create new .gitignore with our entries
        gitignore_path.write_text('\n'.join(gitignore_entries), encoding='utf-8')
#!<

#!> Setup shared state and initialize config/state
def setup_shared_state_and_initialize(project_root):
    print(color('Initializing state and configuration...', Colors.CYAN))

    # Ensure shared_state can resolve the project root
    os.environ['CLAUDE_PROJECT_DIR'] = str(project_root)
    hooks_path = project_root / 'sessions' / 'hooks'
    if str(hooks_path) not in sys.path:
        sys.path.insert(0, str(hooks_path))

    global ss
    try:
        import shared_state as ss  # type: ignore
    except Exception as e:
        print(color('⚠️  Could not import shared_state module after file installation.', Colors.YELLOW))
        print(color(f'Error: {e}', Colors.YELLOW))
        raise

    # Ensure files exist and set a sensible default OS
    try:
        _ = ss.load_config()
    except Exception as e:
        # Attempt to sanitize legacy/bad config keys and retry
        try:
            cfg_path = ss.CONFIG_FILE
            if cfg_path.exists():
                data = json.loads(cfg_path.read_text(encoding='utf-8'))
                ba = data.get('blocked_actions', {})
                if isinstance(ba, dict):
                    allowed = {'implementation_only_tools', 'bash_read_patterns', 'bash_write_patterns', 'extrasafe'}
                    bad_keys = [k for k in list(ba.keys()) if k not in allowed]
                    if bad_keys:
                        for k in bad_keys: ba.pop(k, None)
                        data['blocked_actions'] = ba
                        cfg_path.write_text(json.dumps(data, indent=2), encoding='utf-8')
        except Exception:
            pass
        # Retry; if still fails, back up and reset to defaults
        try:
            _ = ss.load_config()
        except Exception:
            try:
                cfg_path = ss.CONFIG_FILE
                if cfg_path.exists():
                    bad = cfg_path.with_suffix('.bad.json')
                    with contextlib.suppress(Exception): cfg_path.replace(bad)
                _ = ss.load_config()
            except Exception as e2:
                raise e2

    _ = ss.load_state()

    os_name = platform.system()
    os_map = {'Windows': ss.UserOS.WINDOWS, 'Linux': ss.UserOS.LINUX, 'Darwin': ss.UserOS.MACOS}
    detected_os = os_map.get(os_name, ss.UserOS.LINUX)

    with ss.edit_config() as config:
        # Coerce/initialize OS field
        current = getattr(config.environment, 'os', None)
        if isinstance(current, str):
            try:
                config.environment.os = ss.UserOS(current)
            except Exception:
                config.environment.os = detected_os
        elif current is None:
            config.environment.os = detected_os

    # Verify files were created
    state_file = project_root / 'sessions' / 'sessions-state.json'
    config_file = project_root / 'sessions' / 'sessions-config.json'
    if not state_file.exists() or not config_file.exists():
        print(color('⚠️  State files were not created properly', Colors.YELLOW))
        print(color('You may need to initialize them manually on first run', Colors.YELLOW))
#!<

#!> Kickstart cleanup
def kickstart_cleanup(project_root):
    """Delete kickstart files when user skips onboarding, with TUI-friendly info output."""
    info_lines = [color('🧹 Removing kickstart files...', Colors.CYAN)]
    set_info(info_lines)

    sessions_dir = project_root / 'sessions'

    # 1. Delete kickstart hook (Python variant for Python installer)
    py_hook = sessions_dir / 'hooks' / 'kickstart_session_start.py'

    # Update settings.json to swap kickstart hook -> regular session_start hook
    settings = get_settings(project_root)
    updated_settings = False
    try:
        hooks_root = settings.get('hooks', {}) if isinstance(settings, dict) else {}
        session_start_cfgs = hooks_root.get('SessionStart', []) if isinstance(hooks_root, dict) else []
        # Replace kickstart commands with regular ones
        for cfg in session_start_cfgs or []:
            hooks_list = cfg.get('hooks', []) if isinstance(cfg, dict) else []
            for hook in hooks_list:
                cmd = hook.get('command') if isinstance(hook, dict) else None
                if isinstance(cmd, str) and 'kickstart_session_start' in cmd:
                    # Replace the kickstart hook with the regular session_start variant
                    if 'kickstart_session_start.py' in cmd:
                        hook['command'] = cmd.replace('kickstart_session_start.py', 'session_start.py')
                        updated_settings = True
                    elif 'kickstart_session_start.js' in cmd:
                        hook['command'] = cmd.replace('kickstart_session_start.js', 'session_start.js')
                        updated_settings = True
        # De-duplicate any resulting duplicate session_start commands
        commands_seen = set()
        new_cfgs = []
        for cfg in session_start_cfgs or []:
            hooks_list = cfg.get('hooks', []) if isinstance(cfg, dict) else []
            new_hooks = []
            for hook in hooks_list:
                cmd = hook.get('command') if isinstance(hook, dict) else None
                if isinstance(cmd, str):
                    if cmd in commands_seen:
                        updated_settings = True
                        continue
                    commands_seen.add(cmd)
                new_hooks.append(hook)
            if new_hooks:
                cfg['hooks'] = new_hooks
                new_cfgs.append(cfg)
        if isinstance(hooks_root, dict):
            hooks_root['SessionStart'] = new_cfgs
    except Exception as e:
        info_lines.append(color(f'⚠️  Could not update settings.json hooks: {e}', Colors.YELLOW))
        set_info(info_lines)

    if updated_settings:
        if write_settings(project_root, settings):
            info_lines.append(color('✓ Updated .claude/settings.json to use session_start hook', Colors.GREEN))
        else:
            info_lines.append(color('✗ Failed to write updated .claude/settings.json', Colors.RED))
        set_info(info_lines)

    if py_hook.exists():
        py_hook.unlink()
        info_lines.append(color('✓ Deleted kickstart_session_start.py', Colors.GREEN))
        set_info(info_lines)

    # 2. Delete kickstart protocols directory
    protocols_dir = sessions_dir / 'protocols' / 'kickstart'
    if protocols_dir.exists():
        shutil.rmtree(protocols_dir)
        info_lines.append(color('✓ Deleted protocols/kickstart/', Colors.GREEN))
        set_info(info_lines)

    # 3. Delete kickstart setup task
    task_file = sessions_dir / 'tasks' / 'h-kickstart-setup.md'
    if task_file.exists():
        task_file.unlink()
        info_lines.append(color('✓ Deleted h-kickstart-setup.md', Colors.GREEN))
        set_info(info_lines)

    # 4. Remove kickstart API (Python variant) and rely on optional import in router
    py_api = sessions_dir / 'api' / 'kickstart_commands.py'
    if py_api.exists():
        try:
            py_api.unlink()
            info_lines.append(color('✓ Deleted sessions/api/kickstart_commands.py', Colors.GREEN))
        except Exception as e:
            info_lines.append(color(f'⚠️  Could not delete kickstart_commands.py: {e}', Colors.YELLOW))
        set_info(info_lines)

    info_lines.append(color('✓ Kickstart cleanup complete', Colors.GREEN))
    set_info(info_lines)
    return 'Kickstart cleanup complete'
#!<

#!> Restore tasks
def restore_tasks(project_root, backup_dir):
    """Restore tasks from backup after installation."""
    print(color('\n♻️  Restoring tasks...', Colors.CYAN))

    try:
        tasks_backup = backup_dir / 'tasks'
        if tasks_backup.exists():
            tasks_dest = project_root / 'sessions' / 'tasks'
            copy_directory(tasks_backup, tasks_dest)

            task_count = sum(1 for f in tasks_backup.rglob('*.md'))
            print(color(f'   ✓ Restored {task_count} task files', Colors.GREEN))
    except Exception as e:
        print(color(f'   ✗ Restore failed: {e}', Colors.RED))
        print(color(f'   Your backup is safe at: {backup_dir.relative_to(project_root)}/', Colors.YELLOW))
        print(color('   Manually copy files from backup/tasks/ to sessions/tasks/', Colors.YELLOW))
        # Don't raise - let user recover manually

#!<

##-##

## ===== CONFIG QUESTIONS ===== ##

#!> Git preferences
def _ask_default_branch():
    set_info([  color("cc-sessions uses git branches to section off task work and", Colors.CYAN),
                color("merge back to your default work branch when the task is done.", Colors.CYAN), "",
                "Set your default branch...", ""])
    val = input("Claude should merge task branches to (ex. 'main', 'next', 'master', etc.): ") or 'main'
    with ss.edit_config() as conf: conf.git_preferences.default_branch = val
    clear_info()

def _ask_has_submodules():
    val = inquirer.list_input(message="The repo you're installing into is a:", choices=['Monorepo (no submodules)', 'Super-repo (has submodules)'])
    with ss.edit_config() as conf: conf.git_preferences.has_submodules = ('Super-repo' in val)

def _ask_git_add_pattern():
    val = inquirer.list_input(message='When choosing what changes to stage and commit from completed tasks, Claude should:', choices=['Ask me each time', 'Stage all modified files automatically'])
    with ss.edit_config() as conf: conf.git_preferences.add_pattern = ss.GitAddPattern.ASK if 'Ask' in val else ss.GitAddPattern.ALL

def _ask_commit_style():
    val = inquirer.list_input(message="You want Claude's commit messages to be:", choices=['Detailed (multi-line with description)', 'Conventional (type: subject format)', 'Simple (single line)'])
    with ss.edit_config() as conf:
        if 'Detailed' in val: conf.git_preferences.commit_style = ss.GitCommitStyle.OP
        elif 'Conventional' in val: conf.git_preferences.commit_style = ss.GitCommitStyle.REG
        else: conf.git_preferences.commit_style = ss.GitCommitStyle.SIMP

def _ask_auto_merge():
    show_header(print_git_section)
    default_branch = ss.load_config().git_preferences.default_branch
    val = inquirer.list_input(message='During task completion, after comitting changes, Claude should:', choices=[f'Auto-merge to {default_branch}', f'Ask me if I want to merge to {default_branch}'])
    with ss.edit_config() as conf: conf.git_preferences.auto_merge = ('Auto-merge' in val)

def _ask_auto_push():
    show_header(print_git_section)
    val = inquirer.list_input(message='After committing/merging, Claude should:', choices=['Auto-push to remote', 'Ask me if I want to push'])
    with ss.edit_config() as conf: conf.git_preferences.auto_push = ('Auto-push' in val)
#!<

#!> Environment settings
def _ask_developer_name():
    name = input("Claude should call you: ") or 'developer'
    with ss.edit_config() as conf: conf.environment.developer_name = name

def _ask_os():
    os_name = platform.system()
    detected = {'Windows': 'windows', 'Linux': 'linux', 'Darwin': 'macos'}.get(os_name, 'linux')
    val = inquirer.list_input(
        message=f"Detected OS [{color(detected.capitalize(),Colors.YELLOW)}]",
        choices=choices_filtered([
            f'{detected.capitalize()} is correct',
            'Switch to Windows' if detected != 'windows' else None,
            'Switch to macOS' if detected != 'macos' else None,
            'Switch to Linux' if detected != 'linux' else None
        ]),
        default=f'{detected.capitalize()} is correct')
    with ss.edit_config() as conf:
        if 'Windows' in val: conf.environment.os = ss.UserOS.WINDOWS
        elif 'macOS' in val: conf.environment.os = ss.UserOS.MACOS
        elif 'Linux' in val: conf.environment.os = ss.UserOS.LINUX
        else: conf.environment.os = ss.UserOS(detected)

def _ask_shell():
    detected_shell = os.environ.get('SHELL', 'bash').split('/')[-1]
    val = inquirer.list_input(
        message=f"Detected shell [{color(detected_shell,Colors.YELLOW)}]",
        choices=choices_filtered([
            f'{detected_shell} is correct',
            'Switch to bash' if detected_shell != 'bash' else None,
            'Switch to zsh' if detected_shell != 'zsh' else None,
            'Switch to fish' if detected_shell != 'fish' else None,
            'Switch to powershell' if detected_shell != 'powershell' else None,
            'Switch to cmd' if detected_shell != 'cmd' else None
        ]),
        default=f'{detected_shell} is correct')
    with ss.edit_config() as conf:
        if 'bash' in val: conf.environment.shell = ss.UserShell.BASH
        elif 'zsh' in val: conf.environment.shell = ss.UserShell.ZSH
        elif 'fish' in val: conf.environment.shell = ss.UserShell.FISH
        elif 'powershell' in val: conf.environment.shell = ss.UserShell.POWERSHELL
        elif 'cmd' in val: conf.environment.shell = ss.UserShell.CMD
        else:
            try: conf.environment.shell = ss.UserShell(detected_shell)
            except Exception: conf.environment.shell = ss.UserShell.BASH
#!<

#!> Blocked actions
def _edit_bash_read_patterns():
    info = [    color("In Discussion mode, Claude can only use read-like tools (including commands in", Colors.CYAN),
                color("the Bash tool).", Colors.CYAN),
                color("To do this, we parse Claude's Bash tool input in Discussion mode to check for", Colors.CYAN),
                color("write-like and read-only bash commands from a known list.", Colors.CYAN), "",
                "You might have some CLI commands that you want to mark as \"safe\" to use in Discussion mode.",
                "For reference, here are the commands we already auto-approve in Discussion mode:",
                color(', '.join(['cat', 'ls', 'pwd', 'cd', 'echo', 'grep', 'find', 'git status', 'git log']), Colors.YELLOW),
                color(', '.join(['git diff', 'docker ps', 'kubectl get', 'npm list', 'pip show', 'head', 'tail']), Colors.YELLOW),
                color(', '.join(['less', 'more', 'file', 'stat', 'du', 'df', 'ps', 'top', 'htop', 'who', 'w']), Colors.YELLOW),
                color('...(70+ commands total)', Colors.YELLOW), "",
                "Type any additional command you would like to auto-allow and press Enter.",
                "Press Enter on an empty line to finish.", ""]
    set_info(info)
    custom_read = []
    while True:
        cmd = input().strip()
        if not cmd: break
        custom_read.append(cmd)
        added = [color(f"✓ Added {', '.join([cmd for cmd in custom_read[-5:]])}{f'... ({len(custom_read)} total)' if (len(custom_read) > 5) else ''}", Colors.GREEN), ""]
        updated_info = info + added
        set_info(updated_info)

    with ss.edit_config() as conf: conf.blocked_actions.bash_read_patterns = custom_read
    clear_info()

def _edit_bash_write_patterns():
    info = [    color("Similar to the read-only bash commands, we also check for write-like bash", Colors.CYAN),
                color("commands during Discussion mode and block them.", Colors.CYAN), "",
                "You might have some CLI commands that you want to mark as blocked in Discussion mode.",
                "For reference, here are the commands we already block in Discussion mode:",
                color(', '.join(['rm', 'mv', 'cp', 'chmod', 'chown', 'mkdir', 'rmdir', 'systemctl', 'service']), Colors.YELLOW),
                color(', '.join(['apt', 'yum', 'npm install', 'pip install', 'make', 'cmake', 'sudo', 'kill']), Colors.YELLOW),
                color('...(and more)', Colors.YELLOW), "",
                "Type any additional command you would like blocked and press Enter.",
                "Press Enter on an empty line to finish.", ""]
    set_info(info)
    custom_write = []
    while True:
        cmd = input().strip()
        if not cmd: break
        custom_write.append(cmd)
        added = [color(f"✓ Added {', '.join([cmd for cmd in custom_write[-5:]])}{f'... ({len(custom_write)} total)' if (len(custom_write) > 5) else ''}", Colors.GREEN), ""]
        updated_info = info + added
        set_info(updated_info)

    with ss.edit_config() as conf: conf.blocked_actions.bash_write_patterns = custom_write
    clear_info()

def _ask_extrasafe_mode():
    info = [    color("What if Claude uses a bash command in discussion mode that's not in our",Colors.CYAN), 
                color("read-only *or* our write-like list?",Colors.CYAN), "",
                "The 'extrasafe' setting blocks patterns that aren't in our read-only list by default", ""]
    set_info(info)
    val = inquirer.list_input(message="If Claude uses an unknown Bash command, I want to", choices=['Block it (Extrasafe ON)', 'Allow it (Extrasafe OFF)'])
    with ss.edit_config() as conf: conf.blocked_actions.extrasafe = ('ON' in val)
    clear_info()

def _edit_blocked_tools():
    set_info([  "Which Claude Code tools should be blocked in discussion mode?",
                color("*Use Space to toggle, Enter to submit*", Colors.YELLOW),
                color("NOTE: Write-like Bash commands are already blocked", Colors.YELLOW), ""])

    # Default blocked tools
    default_blocked = ['Edit', 'Write', 'MultiEdit', 'NotebookEdit']
    all_tools = ['Edit', 'Write', 'MultiEdit', 'NotebookEdit', 'Bash', 'Read', 'Glob', 'Grep', 'Task', 'TodoWrite']

    blocked_tools = inquirer.checkbox(
        message="Select tools to BLOCK in discussion mode",
        choices=all_tools,
        default=default_blocked
    )
    with ss.edit_config() as conf:
        conf.blocked_actions.implementation_only_tools = []
        for t in blocked_tools:
            try: conf.blocked_actions.implementation_only_tools.append(ss.CCTools(t))
            except Exception: pass
    clear_info()
#!<

#!> Trigger phrases
def _customize_triggers() -> bool:
    yert_text = color('(default: "yert")',Colors.GREEN)
    silence_text = color('(default: "SILENCE")',Colors.GREEN)
    mek_text = color('(default: "mek:")',Colors.GREEN)
    start_text = color('(default: "start^:")',Colors.GREEN)
    finito_text = color('(default: "finito")',Colors.GREEN)
    squish_text = color('(default: "squish")',Colors.GREEN)
    set_info([  color("While you can drive cc-sessions using our slash command API, the preferred way",Colors.CYAN),
                color("is with (somewhat) natural language. To achieve this, we use unique trigger",Colors.CYAN),
                color("phrases that automatically activate the 4 protocols and 2 driving modes in",Colors.CYAN),
                color("cc-sessions:",Colors.CYAN),
                color("╔══════════════════════════════════════════════════════╗", Colors.YELLOW),
                f"{color('║',Colors.YELLOW)}  • Switch to implementation mode {yert_text}   {color('║',Colors.YELLOW)}",
                f"{color('║',Colors.YELLOW)}  • Switch to discussion mode {silence_text}    {color('║',Colors.YELLOW)}",
                f"{color('║',Colors.YELLOW)}  • Create a new task/task file {mek_text}     {color('║',Colors.YELLOW)}",
                f"{color('║',Colors.YELLOW)}  • Start a task/task file {start_text}       {color('║',Colors.YELLOW)}",
                f"{color('║',Colors.YELLOW)}  • Close/complete current task {finito_text}   {color('║',Colors.YELLOW)}",
                f"{color('║',Colors.YELLOW)}  • Compact context mid-task {squish_text}      {color('║',Colors.YELLOW)}",
                color("╚══════════════════════════════════════════════════════╝", Colors.YELLOW), ""])
    customize_triggers = inquirer.list_input(message="Would you like to add any of your own custom trigger phrases?", choices=['Use defaults', 'Customize'])
    clear_info()
    # Ensure sensible defaults exist in config
    with ss.edit_config() as conf:
        tp = conf.trigger_phrases
        # Only set defaults if lists are empty
        if not getattr(tp, 'implementation_mode', None): tp.implementation_mode = ['yert']
        if not getattr(tp, 'discussion_mode', None): tp.discussion_mode = ['SILENCE']
        if not getattr(tp, 'task_creation', None): tp.task_creation = ['mek:']
        if not getattr(tp, 'task_startup', None): tp.task_startup = ['start^:']
        if not getattr(tp, 'task_completion', None): tp.task_completion = ['finito']
        if not getattr(tp, 'context_compaction', None): tp.context_compaction = ['squish']
    return (customize_triggers == 'Customize')


def _edit_triggers_implementation():
    info = [    color("The implementation mode trigger is used when Claude proposes todos for", Colors.CYAN),
                color("implementation that you agree with. Once used, the user_messages hook will", Colors.CYAN),
                color("automatically switch the mode to Implementation, notify Claude, and lock in the", Colors.CYAN),
                color("proposed todo list to ensure Claude doesn't go rogue.", Colors.CYAN), "",
                color("╔════════════════════════════════════════════════════╗", Colors.YELLOW),
                f"{color('║', Colors.YELLOW)}  To add your own custom trigger phrase, think of   {color('║', Colors.YELLOW)}",
                f"{color('║', Colors.YELLOW)}  something that is:                                {color('║',Colors.YELLOW)}",
                f"{color('║                                                    ║',Colors.YELLOW)}",
                f"{color('║',Colors.YELLOW)}     • Easy to remember and type                    {color('║',Colors.YELLOW)}",
                f"{color('║',Colors.YELLOW)}     • Won't ever come up in regular operation      {color('║',Colors.YELLOW)}",
                color("╚════════════════════════════════════════════════════╝",Colors.YELLOW), "",
                color("We recommend using symbols or uppercase for trigger phrases that may otherwise",Colors.CYAN),
                color("be used naturally in conversation (ex. instead of \"stop\", you might use \"STOP\"",Colors.CYAN),
                color("or \"st0p\" or \"--stop\").\n",Colors.CYAN), f"Current phrase: \"yert\"", "",
                "Type a trigger phrase to add and press \"enter\". When you're done, press \"enter\"",
                "again to move on to the next step:", ""]
    set_info(info)
    phrases = []
    while True:
        phrase = input().strip()
        if not phrase: break
        phrases.append(phrase)
        with ss.edit_config() as conf: conf.trigger_phrases.implementation_mode.append(phrase)
        added = [color(f"✓ Added {', '.join([p for p in phrases[-5:]])}{f'... ({len(phrases)} total)' if (len(phrases) > 5) else ''}", Colors.GREEN), ""]
        updated_info = info + added
        set_info(updated_info)
    clear_info()

def _edit_triggers_discussion():
    info = [    color("The discussion mode trigger is an emergency stop that immediately switches", Colors.CYAN),
                color("Claude back to discussion mode. Once used, the user_messages hook will set the", Colors.CYAN),
                color("mode to discussion and inform Claude that they need to re-align.", Colors.CYAN), "",
                f"Current phrase: \"SILENCE\"",
                'Add discussion mode trigger phrases ("stop phrases"). Press Enter on empty line to finish.']
    set_info(info)
    phrases = []
    while True:
        phrase = input().strip()
        if not phrase: break
        phrases.append(phrase)
        with ss.edit_config() as conf: conf.trigger_phrases.discussion_mode.append(phrase)
        added = [color(f"✓ Added {', '.join([p for p in phrases[-5:]])}{f'... ({len(phrases)} total)' if (len(phrases) > 5) else ''}", Colors.GREEN), ""]
        updated_info = info + added
        set_info(updated_info)
    clear_info()

def _edit_triggers_task_creation():
    info = [    color("The task creation trigger activates the task creation protocol. Once used, the", Colors.CYAN),
                color("user_messages hook will load the task creation protocol which guides Claude", Colors.CYAN),
                color("through creating a properly structured task file with priority, success", Colors.CYAN),
                color("criteria, and context manifest.", Colors.CYAN), "",
                f"Current phrase: \"mek:\"", 'Add task creation trigger phrases. Press Enter on empty line to finish.', ""]
    set_info(info)
    phrases = []
    while True:
        phrase = input().strip()
        if not phrase: break
        phrases.append(phrase)
        with ss.edit_config() as conf: conf.trigger_phrases.task_creation.append(phrase)
        added = [color(f"✓ Added {', '.join([p for p in phrases[-5:]])}{f'... ({len(phrases)} total)' if (len(phrases) > 5) else ''}", Colors.GREEN), ""]
        updated_info = info + added
        set_info(updated_info)
    clear_info()

def _edit_triggers_task_startup():
    info = [    color("The task startup trigger activates the task startup protocol. Once used, the", Colors.CYAN),
                color("user_messages hook will load the task startup protocol which guides Claude", Colors.CYAN),
                color("through checking git status, creating branches, gathering context, and", Colors.CYAN),
                color("proposing implementation todos.", Colors.CYAN),"",
                f"Current phrase: \"start^:\"",
                'Add task startup trigger phrases. Press Enter on empty line to finish.']
    set_info(info)
    phrases = []
    while True:
        phrase = input().strip()
        if not phrase: break
        phrases.append(phrase)
        with ss.edit_config() as conf: conf.trigger_phrases.task_startup.append(phrase)
        added = [color(f"✓ Added {', '.join([p for p in phrases[-5:]])}{f'... ({len(phrases)} total)' if (len(phrases) > 5) else ''}", Colors.GREEN), ""]
        updated_info = info + added
        set_info(updated_info)

def _edit_triggers_task_completion():
    info = [    color("The task completion trigger activates the task completion protocol. Once used,", Colors.CYAN),
                color("the user_messages hook will load the task completion protocol which guides", Colors.CYAN),
                color("Claude through running pre-completion checks, committing changes, merging to", Colors.CYAN),
                color("main, and archiving the completed task.", Colors.CYAN),"",
                f"Current phrase: \"finito\"", 'Add task completion trigger phrases. Press Enter on empty line to finish.',""]
    set_info(info)
    phrases = []
    while True:
        phrase = input().strip()
        if not phrase: break
        phrases.append(phrase)
        with ss.edit_config() as conf: conf.trigger_phrases.task_completion.append(phrase)
        added = [color(f"✓ Added {', '.join([p for p in phrases[-5:]])}{f'... ({len(phrases)} total)' if (len(phrases) > 5) else ''}", Colors.GREEN), ""]
        updated_info = info + added
        set_info(updated_info)
    clear_info()

def _edit_triggers_compaction():
    info = [    color("The context compaction trigger activates the context compaction protocol. Once", Colors.CYAN),
                color("used, the user_messages hook will load the context compaction protocol which", Colors.CYAN),
                color("guides Claude through running logging and context-refinement agents to preserve", Colors.CYAN),
                color("task state before the context window fills up.", Colors.CYAN),"",
                f"Current phrase: \"squish\"", 'Add context compaction trigger phrases. Press Enter on empty line to finish.',""]
    set_info(info)
    phrases = []
    while True:
        phrase = input().strip()
        if not phrase: break
        phrases.append(phrase)
        with ss.edit_config() as conf: conf.trigger_phrases.context_compaction.append(phrase)
        added = [color(f"✓ Added {', '.join([p for p in phrases[-5:]])}{f'... ({len(phrases)} total)' if (len(phrases) > 5) else ''}", Colors.GREEN), ""]
        updated_info = info + added
        set_info(updated_info)
    clear_info()
#!<

#!> Feature toggles
def _ask_branch_enforcement():
    set_info([  color("When working on a task, branch enforcement blocks edits to files unless they", Colors.CYAN),
                color("are in a repo that is on the task branch. If in a submodule, the submodule", Colors.CYAN),
                color("also has to be listed in the task file under the \"submodules\" field.", Colors.CYAN), "",
                "This prevents Claude from doing silly things with files outside the scope of",
                "what you're working on, which can happen frighteningly often. But, it may not",
                "be as flexible as you want. *It also doesn't work well with non-Git VCS*.", ""])

    val = inquirer.list_input(message='I want branch enforcement:', choices=['Enabled (recommended for git workflows)', 'Disabled (for alternative VCS like Jujutsu)'])
    with ss.edit_config() as conf: conf.features.branch_enforcement = ('Enabled' in val)
    clear_info()

def _ask_auto_ultrathink():
    set_info([  color("Auto-ultrathink adds \"[[ ultrathink ]]\" to *every message* you submit to", Colors.CYAN),
                color("Claude Code. This is the most robust way to force maximum thinking for every", Colors.CYAN),
                color("message.", Colors.CYAN), "",
                "If you are not a Claude Max x20 subscriber and/or you are budget-conscious,",
                "it's recommended that you disable auto-ultrathink and manually trigger thinking",
                "as needed.", ""])
    val = inquirer.list_input(message='I want auto-ultrathink:', choices=['Enabled', 'Disabled (recommended for budget-conscious users)'])
    with ss.edit_config() as conf: conf.features.auto_ultrathink = (val == 'Enabled')
    clear_info()

def detect_nerd_font_support():
    """Detect if terminal likely supports Nerd Fonts."""
    env = os.environ

    # Known terminals with good Nerd Font support
    good_terms = {
        'iTerm.app', 'iTerm2', 'WezTerm', 'Hyper', 'Alacritty',
        'kitty', 'org.wezterm.wezterm-gui'
    }

    term_program = env.get('TERM_PROGRAM', '')
    term = env.get('TERM', '')
    lc_terminal = env.get('LC_TERMINAL', '')

    # Check for known terminals
    if term_program in good_terms or lc_terminal in good_terms:
        return True, term_program or lc_terminal

    # Kitty sets TERM=xterm-kitty
    if 'kitty' in term.lower():
        return True, 'Kitty'

    # Windows Terminal
    if env.get('WT_SESSION') or env.get('WT_PROFILE_ID'):
        return True, 'Windows Terminal'

    # Conservative default: assume no support
    return False, term or 'unknown'

def _ask_nerd_fonts():
    detected, term_name = detect_nerd_font_support()

    if term_name:
        set_info([
            color(f'Detected terminal: {term_name}', Colors.CYAN),
            ""
        ])

    choices = [
        'Nerd Fonts (I have Nerd Fonts installed)',
        'Emoji fallback',
        'ASCII fallback (maximum compatibility)'
    ]
    # Default to Nerd Fonts if detected, Emoji if not
    default_choice = choices[0] if detected else choices[1]

    val = inquirer.list_input(
        message='I want icons in statusline:',
        choices=choices,
        default=default_choice
    )

    # Map choice to IconStyle enum
    with ss.edit_config() as conf:
        if 'Nerd Fonts' in val:
            conf.features.icon_style = ss.IconStyle.NERD_FONTS
        elif 'Emoji' in val:
            conf.features.icon_style = ss.IconStyle.EMOJI
        else:  # ASCII
            conf.features.icon_style = ss.IconStyle.ASCII

    clear_info()

def _ask_context_warnings():
    val = inquirer.list_input(message='I want Claude to be warned to suggest compacting context at:', choices=['85% and 90%', '90%', 'Never'])
    with ss.edit_config() as conf:
        if 'and' in val:
            conf.features.context_warnings.warn_85 = True
            conf.features.context_warnings.warn_90 = True
        elif '90' in val:
            conf.features.context_warnings.warn_85 = False
            conf.features.context_warnings.warn_90 = True
        else:
            conf.features.context_warnings.warn_85 = False
            conf.features.context_warnings.warn_90 = False

def _ask_statusline():
    set_info([  color('cc-sessions includes a statusline that shows context usage, mode',Colors.CYAN),
                color('current task, git branch, open tasks, and uncommitted files.',Colors.CYAN), ""])
    val = inquirer.list_input(message="Would you like to use it?", choices=['Yes, use cc-sessions statusline', 'No, I have my own statusline'])
    if 'Yes' in val:
        settings_file = ss.PROJECT_ROOT / '.claude' / 'settings.json'
        if settings_file.exists():
            with open(settings_file, 'r') as f: settings = json.load(f)
        else: settings = {}

        # Use Windows or Unix path syntax based on platform
        is_windows = sys.platform == 'win32'
        statusline_cmd = 'python "%CLAUDE_PROJECT_DIR%\\sessions\\statusline.py"' if is_windows else 'python $CLAUDE_PROJECT_DIR/sessions/statusline.py'

        settings['statusLine'] = {'type': 'command', 'command': statusline_cmd}
        with open(settings_file, 'w') as f: json.dump(settings, f, indent=2)
        set_info([color('✓ Statusline configured in .claude/settings.json', Colors.GREEN)])
        sleep(0.5)
    else:
        # Show platform-appropriate example
        is_windows = sys.platform == 'win32'
        example_cmd = 'python "%CLAUDE_PROJECT_DIR%\\sessions\\statusline.py"' if is_windows else 'python $CLAUDE_PROJECT_DIR/sessions/statusline.py'

        set_info([  color('You can add the cc-sessions statusline later by adding this to .claude/settings.json:', Colors.YELLOW),
                    color('{',Colors.YELLOW), color('  "statusLine": {',Colors.YELLOW), color('    "type": "command",',Colors.YELLOW),
                    color(f'    "command": "{example_cmd}"',Colors.YELLOW), color('  }',Colors.YELLOW),
                    color('}', Colors.YELLOW),""])
        input('Press enter to continue...')
    return True if 'Yes' in val else False
#!<

##-##

## ===== CONFIG PHASES ===== ##

def run_full_configuration():
    show_header(print_config_header)
    cfg = {'git_preferences': {}, 'environment': {}, 'blocked_actions': {}, 'trigger_phrases': {}, 'features': {}}

    #!> Gather git preferences
    show_header(print_git_section)
    _ask_default_branch()
    _ask_has_submodules()
    _ask_git_add_pattern()
    _ask_commit_style()
    _ask_auto_merge()
    _ask_auto_push()
    #!<

    #!> Gather environment settings
    show_header(print_env_section)
    _ask_developer_name()
    _ask_os()
    _ask_shell()
    #!<

    #!> Gather blocked actions
    show_header(print_read_only_section)
    _edit_bash_read_patterns()

    show_header(print_write_like_section)
    _edit_bash_write_patterns()

    show_header(print_extrasafe_section)
    _ask_extrasafe_mode()

    show_header(print_blocking_header)
    _edit_blocked_tools()
    #!<

    #!> Gather trigger phrases
    show_header(print_triggers_header)
    wants_customization = _customize_triggers()
    if wants_customization:
        show_header(print_go_triggers_section)
        _edit_triggers_implementation()

        show_header(print_no_triggers_section)
        _edit_triggers_discussion()

        show_header(print_create_section)
        _edit_triggers_task_creation()

        show_header(print_startup_section)
        _edit_triggers_task_startup()

        show_header(print_complete_section)
        _edit_triggers_task_completion()

        show_header(print_compact_section)
        _edit_triggers_compaction()
    #!<

    #!> Ask about statusline
    show_header(print_statusline_header)
    statusline_installed = _ask_statusline()
    #!<

    #!> Gather feature toggles
    show_header(print_features_header)

    _ask_branch_enforcement()
    _ask_auto_ultrathink()
    if statusline_installed: _ask_nerd_fonts()
    _ask_context_warnings()
    #!<

    print(color('\n✓ Configuration complete!\n', Colors.GREEN))


def run_config_editor(project_root):
    """Interactive config editor"""
    show_header(print_config_header)
    set_info([  color('How to use:', Colors.CYAN),
                color('- Use j/k or arrows to navigate, Enter to select',Colors.CYAN),
                color('- Choose Back to return, Done to finish',Colors.CYAN),
                color('- You can also press Ctrl+C to exit anytime',Colors.CYAN), ""])

    settings_path = project_root / '.claude' / 'settings.json'

    def _statusline_installed() -> bool:
        try:
            data = json.loads(settings_path.read_text(encoding='utf-8')) if settings_path.exists() else {}
            cmd = (data.get('statusLine') or {}).get('command')
            return bool(cmd and 'sessions/statusline.py' in cmd)
        except Exception: return False

    def _fmt_bool(v: bool) -> str: return 'Enabled' if v else 'Disabled'

    def _fmt_enum(v) -> str:
        try: return getattr(v, 'value', str(v))
        except Exception: return str(v)

    def _fmt_list(xs) -> str:
        try: return ', '.join([x for x in xs if x]) if xs else 'None'
        except Exception: return 'None'

    def _fmt_tools(xs) -> str:
        try: return ', '.join([getattr(x, 'value', str(x)) for x in xs]) if xs else 'None'
        except Exception: return 'None'

    def _reload():
        cfg: ss.SessionsConfig = ss.load_config()
        return cfg, _statusline_installed()

    def _git_menu():
        show_header(print_git_section)
        cfg, _ = _reload()
        g = cfg.git_preferences
        actions = [ (f"{color('Default branch',Colors.RESET)} | {color(_fmt_enum(g.default_branch),Colors.YELLOW)}", _ask_default_branch),
                    (f"{color('Has submodules',Colors.RESET)} | {color(_fmt_enum(g.has_submodules),Colors.YELLOW)}", _ask_has_submodules),
                    (f"{color('Staging pattern',Colors.RESET)} | {color(_fmt_enum(g.add_pattern),Colors.YELLOW)}", _ask_git_add_pattern),
                    (f"{color('Commit style',Colors.RESET)} | {color(_fmt_enum(g.commit_style),Colors.YELLOW)}", _ask_commit_style),
                    (f"{color('Auto-merge',Colors.RESET)} | {color(_fmt_enum(g.auto_merge),Colors.YELLOW)}", _ask_auto_merge),
                    (f"{color('Auto-push',Colors.RESET)} | {color(_fmt_enum(g.auto_push),Colors.YELLOW)}", _ask_auto_push),
                    (color("Back",Colors.YELLOW), None),]
        labels = [lbl for (lbl, _) in actions]
        while True:
            choice = inquirer.list_input(message=f"{color('[Setting]',Colors.RESET)} | {color('[Current Value]',Colors.YELLOW)}\n", choices=labels)
            if 'Back' in choice: break
            fn = dict(actions).get(choice)
            if fn: fn()
            cfg, _ = _reload()
            g = cfg.git_preferences
            actions[0] = (f"{color('Default branch',Colors.RESET)} | {color(_fmt_enum(g.default_branch),Colors.YELLOW)}", _ask_default_branch)
            actions[1] = (f"{color('Has submodules',Colors.RESET)} | {color(_fmt_enum(g.has_submodules),Colors.YELLOW)}", _ask_has_submodules)
            actions[2] = (f"{color('Staging pattern',Colors.RESET)} | {color(_fmt_enum(g.add_pattern),Colors.YELLOW)}", _ask_git_add_pattern)
            actions[3] = (f"{color('Commit style',Colors.RESET)} | {color(_fmt_enum(g.commit_style),Colors.YELLOW)}", _ask_commit_style)
            actions[4] = (f"{color('Auto-merge',Colors.RESET)} | {color(_fmt_enum(g.auto_merge),Colors.YELLOW)}", _ask_auto_merge)
            actions[5] = (f"{color('Auto-push',Colors.RESET)} | {color(_fmt_enum(g.auto_push),Colors.YELLOW)}", _ask_auto_push)
            labels[:] = [lbl for (lbl, _) in actions]

    def _env_menu():
        show_header(print_env_section)
        cfg, _ = _reload()
        e = cfg.environment
        actions = [ (f"Developer name | {color(_fmt_enum(e.developer_name),Colors.YELLOW)}", _ask_developer_name),
                    (f"Operating system | {color(_fmt_enum(e.os),Colors.YELLOW)}", _ask_os),
                    (f"Shell | {color(_fmt_enum(e.shell),Colors.YELLOW)}", _ask_shell),
                    (color("Back",Colors.YELLOW), None),]
        labels = [lbl for (lbl, _) in actions]
        while True:
            choice = inquirer.list_input(message=f"{color('[Setting]',Colors.RESET)} | {color('[Current Value]',Colors.YELLOW)}\n", choices=labels)
            if 'Back' in choice: break
            fn = dict(actions).get(choice)
            if fn: fn()
            cfg, _ = _reload(); e = cfg.environment
            actions[0] = (f"Developer name | {color(_fmt_enum(e.developer_name),Colors.YELLOW)}", _ask_developer_name)
            actions[1] = (f"Operating system | {color(_fmt_enum(e.os),Colors.YELLOW)}", _ask_os)
            actions[2] = (f"Shell | {color(_fmt_enum(e.shell),Colors.YELLOW)}", _ask_shell)
            labels[:] = [lbl for (lbl, _) in actions]

    def _blocked_menu():
        show_header(print_blocking_header)
        cfg, _ = _reload()
        b = cfg.blocked_actions
        actions = [ (f"Tools list | {color(_fmt_tools(b.implementation_only_tools),Colors.YELLOW)}", _edit_blocked_tools),
                    (f"Bash read-only | {color(_fmt_list(b.bash_read_patterns),Colors.YELLOW)}", _edit_bash_read_patterns),
                    (f"Bash write-like | {color(_fmt_list(b.bash_write_patterns),Colors.YELLOW)}", _edit_bash_write_patterns),
                    (f"Extrasafe mode | {color(_fmt_bool(b.extrasafe),Colors.YELLOW)}", _ask_extrasafe_mode),
                    (color("Back",Colors.YELLOW), None),]
        labels = [lbl for (lbl, _) in actions]
        while True:
            choice = inquirer.list_input(message=f"{color('[Setting]',Colors.RESET)} | {color('[Current Value]',Colors.YELLOW)}\n", choices=labels)
            if 'Back' in choice: break
            fn = dict(actions).get(choice)
            if fn:
                if 'Bash read-only' in choice: show_header(print_read_only_section)
                elif 'Bash write-like' in choice: show_header(print_write_like_section)
                elif 'Extrasafe' in choice: show_header(print_extrasafe_section)
                fn()
                show_header(print_blocking_header)
            cfg, _ = _reload(); b = cfg.blocked_actions
            actions[0] = (f"Tools list | {color(_fmt_tools(b.implementation_only_tools),Colors.YELLOW)}", _edit_blocked_tools)
            actions[1] = (f"Bash read-only | {color(_fmt_list(b.bash_read_patterns),Colors.YELLOW)}", _edit_bash_read_patterns)
            actions[2] = (f"Bash write-like | {color(_fmt_list(b.bash_write_patterns),Colors.YELLOW)}", _edit_bash_write_patterns)
            actions[3] = (f"Extrasafe mode | {color(_fmt_bool(b.extrasafe),Colors.YELLOW)}", _ask_extrasafe_mode)
            labels[:] = [lbl for (lbl, _) in actions]

    def _triggers_menu():
        show_header(print_triggers_header)
        cfg, _ = _reload(); t = cfg.trigger_phrases
        actions = [ (f"Implementation mode | {color(_fmt_list(t.implementation_mode),Colors.YELLOW)}", _edit_triggers_implementation),
                    (f"Discussion mode | {color(_fmt_list(t.discussion_mode),Colors.YELLOW)}", _edit_triggers_discussion),
                    (f"Task creation | {color(_fmt_list(t.task_creation),Colors.YELLOW)}", _edit_triggers_task_creation),
                    (f"Task startup | {color(_fmt_list(t.task_startup),Colors.YELLOW)}", _edit_triggers_task_startup),
                    (f"Task completion | {color(_fmt_list(t.task_completion),Colors.YELLOW)}", _edit_triggers_task_completion),
                    (f"Context compaction | {color(_fmt_list(t.context_compaction),Colors.YELLOW)}", _edit_triggers_compaction),
                    (color("Back",Colors.YELLOW), None),]
        labels = [lbl for (lbl, _) in actions]
        while True:
            choice = inquirer.list_input(message=f"{color('[Setting]',Colors.RESET)} | {color('[Current Value]',Colors.YELLOW)}\n", choices=labels)
            if 'Back' in choice: break
            fn = dict(actions).get(choice)
            if fn:
                if 'Implementation mode' in choice: show_header(print_go_triggers_section)
                elif 'Discussion mode' in choice: show_header(print_no_triggers_section)
                elif 'Task creation' in choice: show_header(print_create_section)
                elif 'Task startup' in choice: show_header(print_startup_section)
                elif 'Task completion' in choice: show_header(print_complete_section)
                elif 'Context compaction' in choice: show_header(print_compact_section)
                fn()
                show_header(print_triggers_header)
            cfg, _ = _reload(); t = cfg.trigger_phrases
            actions[0] = (f"Implementation mode | {_fmt_list(t.implementation_mode)}", _edit_triggers_implementation)
            actions[1] = (f"Discussion mode | {color(_fmt_list(t.discussion_mode),Colors.YELLOW)}", _edit_triggers_discussion)
            actions[2] = (f"Task creation | {color(_fmt_list(t.task_creation),Colors.YELLOW)}", _edit_triggers_task_creation)
            actions[3] = (f"Task startup | {color(_fmt_list(t.task_startup),Colors.YELLOW)}", _edit_triggers_task_startup)
            actions[4] = (f"Task completion | {color(_fmt_list(t.task_completion),Colors.YELLOW)}", _edit_triggers_task_completion)
            actions[5] = (f"Context compaction | {color(_fmt_list(t.context_compaction),Colors.YELLOW)}", _edit_triggers_compaction)
            labels[:] = [lbl for (lbl, _) in actions]

    def _features_menu():
        show_header(print_features_header)
        cfg, installed = _reload(); f = cfg.features
        cw = []
        if getattr(f.context_warnings, 'warn_85', False): cw.append('85%')
        if getattr(f.context_warnings, 'warn_90', False): cw.append('90%')
        cw_str = ', '.join(cw) if cw else 'Never'

        actions = [ (f"Statusline integration | {color('Installed' if installed else 'Not installed',Colors.YELLOW)}", _ask_statusline),
                    (f"Branch enforcement | {color(_fmt_bool(f.branch_enforcement),Colors.YELLOW)}", _ask_branch_enforcement),
                    (f"Auto-ultrathink | {color(_fmt_bool(f.auto_ultrathink),Colors.YELLOW)}", _ask_auto_ultrathink),
                    (f"Nerd Fonts | {color(_fmt_bool(f.use_nerd_fonts),Colors.YELLOW)}", _ask_nerd_fonts) if installed else None,
                    (f"Context warnings | {color(cw_str,Colors.YELLOW)}", _ask_context_warnings),
                    (color("Back",Colors.YELLOW), None),]
        actions = [a for a in actions if a]
        labels = [lbl for (lbl, _) in actions]
        while True:
            choice = inquirer.list_input(message=f"{color('[Setting]',Colors.RESET)} | {color('[Current Value]',Colors.YELLOW)}\n", choices=labels)
            if 'Back' in choice: break
            fn = dict(actions).get(choice)
            if fn:
                if 'Statusline integration' in choice: show_header(print_statusline_header)
                fn()
                show_header(print_features_header)
            cfg, installed = _reload(); f = cfg.features
            cw = []
            if getattr(f.context_warnings, 'warn_85', False): cw.append('85%')
            if getattr(f.context_warnings, 'warn_90', False): cw.append('90%')
            cw_str = ', '.join(cw) if cw else 'Never'
            actions = [ (f"Statusline integration | {color('Installed' if installed else 'Not installed',Colors.YELLOW)}", _ask_statusline),
                        (f"Branch enforcement | {color(_fmt_bool(f.branch_enforcement),Colors.YELLOW)}", _ask_branch_enforcement),
                        (f"Auto-ultrathink | {color(_fmt_bool(f.auto_ultrathink),Colors.YELLOW)}", _ask_auto_ultrathink),
                        (f"Nerd Fonts | {color(_fmt_bool(f.use_nerd_fonts),Colors.YELLOW)}", _ask_nerd_fonts) if installed else None,
                        (f"Context warnings | {color(cw_str,Colors.YELLOW)}", _ask_context_warnings),
                        (color("Back",Colors.YELLOW), None),]
            actions = [a for a in actions if a]
            labels[:] = [lbl for (lbl, _) in actions]

    # Main menu: grouped categories to avoid long scrolling
    while True:
        try:
            show_header(print_config_header)
            choice = inquirer.list_input(
                message='Config Editor — choose a category',
                choices=[   f"{color('Git Preferences', Colors.CYAN)} {color('(default branch, submodules, staging pattern, commit style, auto-merge, auto-push)', Colors.GRAY)}",
                            f"{color('Environment', Colors.CYAN)} {color('(developer name, operating system, shell)', Colors.GRAY)}",
                            f"{color('Blocked Actions', Colors.CYAN)} {color('(tools, read-only commands, write-like commands, extrasafe)', Colors.GRAY)}",
                            f"{color('Trigger Phrases', Colors.CYAN)} {color('(implementation, discussion, task create/start/complete, compaction)', Colors.GRAY)}",
                            f"{color('Features', Colors.CYAN)} {color('(statusline, branch enforcement, ultrathink, context warnings, Nerd Fonts)', Colors.GRAY)}",
                            color('Done',Colors.RED)])
        except KeyboardInterrupt: break

        norm = _strip_ansi(choice)
        if 'Done' in choice:
            clear_info()
            break
        elif norm.startswith('Git Preferences'): _git_menu()
        elif norm.startswith('Environment'): _env_menu()
        elif norm.startswith('Blocked Actions'): _blocked_menu()
        elif norm.startswith('Trigger Phrases'): _triggers_menu()
        elif norm.startswith('Features'): _features_menu()
        else: continue # Shouldn't happen, but continue gracefully
##-##

## ===== IMPORT CONFIG ===== ##
def import_config(project_root: Path, source: str, source_type: str, info: list) -> bool:
    """Import configuration and selected agents from a local dir, Git URL, or GitHub stub.
    Returns True on success (config or any agent imported).
    """
    tmp_to_remove: Path | None = None
    imported_any = False
    try:
        # Resolve source to a local directory path
        if source_type == 'GitHub stub (owner/repo)':
            owner_repo = source.strip().strip('/')
            url = f"https://github.com/{owner_repo}.git"
            tmp_to_remove = Path(tempfile.mkdtemp(prefix='ccs-import-'))
            try: subprocess.run(['git', 'clone', '--depth', '1', url, str(tmp_to_remove)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except Exception as e:
                set_info(info + [color(f'Git clone failed for {url}: {e}', Colors.RED), ""])
                return False
            src_path = tmp_to_remove
        elif source_type == 'Git repository URL':
            url = source.strip()
            tmp_to_remove = Path(tempfile.mkdtemp(prefix='ccs-import-'))
            try: subprocess.run(['git', 'clone', '--depth', '1', url, str(tmp_to_remove)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except Exception as e:
                set_info(info + [color(f'Git clone failed for {url}: {e}', Colors.RED), ""])
                return False
            src_path = tmp_to_remove
        else:
            # Local directory
            src_path = Path(source).expanduser().resolve()
            if not src_path.exists() or not src_path.is_dir():
                set_info(info + [color('Provided path does not exist or is not a directory.', Colors.RED), ""])
                return False

        # sessions-config.json from repo_root/sessions/
        src_cfg = (src_path / 'sessions' / 'sessions-config.json')
        dst_cfg = (project_root / 'sessions' / 'sessions-config.json')
        if src_cfg.exists():
            dst_cfg.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_cfg, dst_cfg)
            set_info(info + [color('✓ Imported sessions-config.json', Colors.GREEN), ""])
            imported_any = True
        else: set_info(info + [color('No sessions-config.json found to import at sessions/sessions-config.json', Colors.YELLOW), ""])

        # Agents: present baseline agent files for choice
        src_agents = src_path / '.claude' / 'agents'
        dst_agents = project_root / '.claude' / 'agents'
        if src_agents.exists():
            for agent_name in AGENT_BASELINE:
                src_file = src_agents / agent_name
                dst_file = dst_agents / agent_name
                if src_file.exists():
                    choice = inquirer.list_input(
                        message=f"Agent '{agent_name}' found in import. Which version to keep?",
                        choices=['Use imported version', 'Keep default']
                    )
                    if choice == 'Use imported version':
                        dst_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src_file, dst_file)
                        set_info(info + [color(f"✓ Imported agent: {agent_name}", Colors.GREEN), ""])
                        imported_any = True
        else: set_info(info + [color('No .claude/agents directory found to import agents from', Colors.YELLOW), ""])

        # Reload config/state
        setup_shared_state_and_initialize(project_root)
        return imported_any
    except Exception as e:
        set_info(info + [color(f'Import failed: {e}', Colors.RED), ""])
        return False
    finally:
        if tmp_to_remove is not None:
            with contextlib.suppress(Exception): shutil.rmtree(tmp_to_remove)

def kickstart_decision(project_root: Path) -> str:
    """Prompt user for kickstart onboarding preference and set state/cleanup accordingly.
    Returns one of: 'full', 'subagents', 'skip'.
    """
    show_header(print_kickstart_header)
    set_info([  color("cc-sessions is an opinionated interactive workflow. You can learn how to use",Colors.CYAN),
                color("it with Claude Code via a custom \"session\" called kickstart.",Colors.CYAN), "",
                "Kickstart will:",
                "  • Teach you the features of cc-sessions",
                "  • Help you set up your first task",
                "  • Show the 4 core protocols you can run",
                "  • Help customize subagents for your codebase", "",
                "Time: 15–30 minutes", ""])

    choice = inquirer.list_input(
        message="Would you like to run kickstart on your first session?",
        choices=[
            'Yes (auto-start full kickstart tutorial)',
            'Just subagents (customize subagents but skip tutorial)',
            'No (skip tutorial, remove kickstart files)'
        ]
    )

    clear_info()
    if 'Yes' in choice:
        with ss.edit_state() as s: s.metadata['kickstart'] = {'mode': 'full'}
        print(color('\n✓ Kickstart will auto-start on your first session', Colors.GREEN))
        return 'full'

    if 'Just subagents' in choice:
        with ss.edit_state() as s: s.metadata['kickstart'] = {'mode': 'subagents'}
        print(color('\n✓ Kickstart will guide you through subagent customization only', Colors.GREEN))
        return 'subagents'

    # Skip
    print(color('\n⏭️  Skipping kickstart onboarding...', Colors.CYAN))
    kickstart_cleanup(project_root)
    return 'skip'
##-##

#-#

# ===== ENTRYPOINT ===== #
def main():
    global ss
    SCRIPT_DIR = get_package_root()
    PROJECT_ROOT = get_project_root()

    #!> Check if already installed and backup if needed
    sessions_dir = PROJECT_ROOT / 'sessions'
    backup_dir = None

    if sessions_dir.exists():
        # Check if there's actual content to preserve
        tasks_dir = sessions_dir / 'tasks'
        has_content = tasks_dir.exists() and any(tasks_dir.rglob('*.md'))

        if not has_content: print(color('🆕 Detected empty sessions directory, treating as fresh install', Colors.CYAN))
        else: print(color('🔍 Detected existing cc-sessions installation', Colors.CYAN)); backup_dir = create_backup(PROJECT_ROOT)
    #!<

    #!> Check for and handle v0.2.6/v0.2.7 migration (with TUI for interactive prompt)
    with tui_session():
        v026_archive_info = run_v026_migration(PROJECT_ROOT)
    #!<

    print(color(f'\n⚙️  Installing cc-sessions to: {PROJECT_ROOT}', Colors.CYAN))
    print()

    try:
        # Phase: install files
        create_directory_structure(PROJECT_ROOT)
        copy_files(SCRIPT_DIR, PROJECT_ROOT)
        configure_settings(PROJECT_ROOT)
        configure_claude_md(PROJECT_ROOT)
        configure_gitignore(PROJECT_ROOT)

        # Phase: load shared state and initialize defaults
        setup_shared_state_and_initialize(PROJECT_ROOT)

        # Phase: interactive portions under TUI
        with tui_session():
            # Decision point (import vs full config)
            did_import = installer_decision_flow(PROJECT_ROOT, v026_archive_info['detected'])

            # Configuration
            if did_import: run_config_editor(PROJECT_ROOT) # tweak imported settings
            else: run_full_configuration()

            # Kickstart decision
            kickstart_mode = kickstart_decision(PROJECT_ROOT)
        
        # Restore tasks if this was an update
        if backup_dir:
            restore_tasks(PROJECT_ROOT, backup_dir)
            print(color(f'\n📁 Backup saved at: {backup_dir.relative_to(PROJECT_ROOT)}/', Colors.CYAN))
            print(color('   (Agents backed up for manual restoration if needed)', Colors.CYAN))

        # Output final message
        print(color('\n✅ cc-sessions installed successfully!\n', Colors.GREEN))

        # Show v0.2.6/v0.2.7 archive message if applicable
        if v026_archive_info.get('archived'):
            print(color('📁 Old v0.2.6/v0.2.7 files archived', Colors.CYAN))
            print(color(f'   Location: {v026_archive_info["path"]}', Colors.CYAN))
            print(color(f'   Files: {v026_archive_info["file_count"]} archived for safekeeping\n', Colors.CYAN))

        print(color('Next steps:', Colors.BOLD))
        # Read current trigger phrases from config for helpful onboarding
        try:
            cfg = ss.load_config()
            t = getattr(cfg, 'trigger_phrases', None)
        except Exception:
            t = None
        def _fmt(xs):
            try: return ', '.join([x for x in (xs or []) if x]) or 'None'
            except Exception: return 'None'

        if kickstart_mode in ('full', 'subagents'):
            print('  1. In your terminal, run: claude')
            print("  2. At the prompt, type: kickstart\n")
        else:  # skip
            print('  1. Create your first task using a trigger:')
            print(f"     - Task creation: {color(_fmt(getattr(t, 'task_creation', None)), Colors.YELLOW)}")
            print(f"     - Task startup:  {color(_fmt(getattr(t, 'task_startup', None)), Colors.YELLOW)}")
            print(f"     - Implementation: {color(_fmt(getattr(t, 'implementation_mode', None)), Colors.YELLOW)}")
            print(f"     - Discussion:    {color(_fmt(getattr(t, 'discussion_mode', None)), Colors.YELLOW)}")
            print(f"     - Completion:    {color(_fmt(getattr(t, 'task_completion', None)), Colors.YELLOW)}")
            print(f"     - Compaction:    {color(_fmt(getattr(t, 'context_compaction', None)), Colors.YELLOW)}\n")

        if backup_dir: print(color('Note: Check backup/ for any custom agents you want to restore\n', Colors.CYAN))


    except Exception as error:
        print(color(f'\n❌ Installation failed: {error}', Colors.RED), file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def installer_decision_flow(project_root, had_v026_artifacts=False):
    """
    Decision point: detect returning users and optionally import config/agents.
    Returns True if a config import occurred and succeeded.

    Args:
        project_root: Path to project root
        had_v026_artifacts: If True, skip first-time question (user definitely not new)
    """
    show_header(print_installer_header)

    did_import = False

    # Skip first-time question if we detected v0.2.6/v0.2.7 artifacts
    if had_v026_artifacts:
        first_time = 'No'
    else:
        first_time = inquirer.list_input(message="Is this your first time using cc-sessions?", choices=['Yes', 'No'])

    if first_time == 'No':
        version_check = inquirer.list_input(message="Have you used cc-sessions v0.3.0 or later (released October 2025)?", choices=['Yes', 'No'])
        if version_check == 'Yes':
            import_choice = inquirer.list_input(message="Would you like to import your configuration and agents?", choices=['Yes', 'No'])
            if import_choice == 'Yes':
                info = [    color('We can import your config and, optionally, agents from Github (URL or stub) or', Colors.CYAN),
                            color('a project folder on your local machine.', Colors.CYAN), ""]
                set_info(info)
                import_source = inquirer.list_input(
                    message="Where is your cc-sessions configuration?",
                    choices=['Local directory', 'Git repository URL', 'GitHub stub (owner/repo)', 'Skip import'])
                if import_source != 'Skip import':
                    if 'Local' in import_source: source_path = input("Path to project: ").strip()
                    elif 'URL' in import_source: source_path = input("Github URL: ")
                    elif 'stub' in import_source: source_path = input("Github stub (i.e. author/repo_name): ")
                    set_info(info + [color(f"Steady lads - importing from {source_path}...", Colors.YELLOW)])
                    did_import = import_config(project_root, source_path, import_source, info)
                    if not did_import:
                        print(color('\nImport failed or not implemented. Continuing with configuration...', Colors.YELLOW))
                else:
                    print(color('\nSkipping import. Continuing with configuration...', Colors.CYAN))
            else:
                print(color('\nContinuing with configuration...', Colors.CYAN))
        else:
            print(color('\nContinuing with configuration...', Colors.CYAN))

    return did_import

#-#

if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(color(f'\n❌ Fatal error: {error}', Colors.RED), file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
#-#

# Enter and set global, SCRIPT_DIR, and PROJECT_ROOT
# Check for previous installation, throw to backup if needed
