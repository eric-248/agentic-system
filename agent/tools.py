"""Tools for the coding agent: run commands, read/write files in ../app."""

import subprocess
from pathlib import Path

# App root: ../app relative to this file (agent/tools.py -> agent/ -> app)
AGENT_DIR = Path(__file__).resolve().parent
APP_ROOT = (AGENT_DIR / ".." / "app").resolve()


def _resolve_app_path(path: str, app_root: Path) -> Path:
    """Resolve path relative to app_root; raise if it escapes app_root."""
    resolved = (app_root / path).resolve()
    if not resolved.is_relative_to(app_root):
        raise ValueError(f"Path escapes app root: {path}")
    return resolved


def _run_command(cmd: str, cwd: str | None = None, *, app_root: Path) -> str:
    """Run a shell command. If cwd is '../app' or None, run from app_root."""
    run_cwd = app_root
    if cwd is not None and cwd != "../app":
        candidate = (AGENT_DIR / cwd).resolve() if not Path(cwd).is_absolute() else Path(cwd)
        if candidate.is_dir():
            run_cwd = candidate
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=run_cwd,
            capture_output=True,
            text=True,
            timeout=300,
        )
        parts = [f"exit_code={result.returncode}"]
        if result.stdout:
            parts.append(f"stdout:\n{result.stdout}")
        if result.stderr:
            parts.append(f"stderr:\n{result.stderr}")
        return "\n".join(parts)
    except subprocess.TimeoutExpired:
        return "Error: command timed out after 300s"
    except Exception as e:
        return f"Error running command: {e}"


def _read_file(path: str, app_root: Path) -> str:
    """Read a file from app. Path is relative to the app root."""
    try:
        full = _resolve_app_path(path, app_root)
        return full.read_text(encoding="utf-8", errors="replace")
    except ValueError as e:
        return str(e)
    except FileNotFoundError:
        return f"Error: file not found: {path}"
    except IsADirectoryError:
        return f"Error: path is a directory, not a file: {path}"
    except Exception as e:
        return f"Error reading file: {e}"


def _write_file(path: str, contents: str, app_root: Path) -> str:
    """Write contents to a file in app. Path is relative to the app root. Creates parent dirs if needed."""
    try:
        full = _resolve_app_path(path, app_root)
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(contents, encoding="utf-8")
        return f"Wrote {path}"
    except ValueError as e:
        return str(e)
    except Exception as e:
        return f"Error writing file: {e}"


def run_command(cmd: str, cwd: str | None = None) -> str:
    """Run a shell command. Uses default APP_ROOT. For parameterized app_root, use get_tool_functions()."""
    return _run_command(cmd, cwd, APP_ROOT)


def read_file(path: str) -> str:
    """Read a file from ../app. Uses default APP_ROOT. For parameterized app_root, use get_tool_functions()."""
    return _read_file(path, APP_ROOT)


def write_file(path: str, contents: str) -> str:
    """Write contents to a file in ../app. Uses default APP_ROOT. For parameterized app_root, use get_tool_functions()."""
    return _write_file(path, contents, APP_ROOT)


def get_tool_functions(app_root: Path) -> dict[str, callable]:
    """Return tool functions bound to the given app_root for use by run_agent_task."""
    from functools import partial

    return {
        "run_command": partial(_run_command, app_root=app_root),
        "read_file": partial(_read_file, app_root=app_root),
        "write_file": partial(_write_file, app_root=app_root),
    }
