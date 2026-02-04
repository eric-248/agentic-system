"""Tools for the coding agent: run commands, read/write files in ../app."""

import subprocess
from pathlib import Path

# App root: ../app relative to this file (agent/tools.py -> agent/ -> app)
AGENT_DIR = Path(__file__).resolve().parent
APP_ROOT = (AGENT_DIR / ".." / "app").resolve()


def _resolve_app_path(path: str) -> Path:
    """Resolve path relative to APP_ROOT; raise if it escapes APP_ROOT."""
    resolved = (APP_ROOT / path).resolve()
    if not resolved.is_relative_to(APP_ROOT):
        raise ValueError(f"Path escapes app root: {path}")
    return resolved


def run_command(cmd: str, cwd: str | None = None) -> str:
    """Run a shell command. If cwd is provided (e.g. '../app'), run from that directory.

    Working directory is resolved relative to the agent directory so cwd='../app'
    runs from the app root. Returns a string with stdout, stderr, and exit code.
    """
    if cwd is None:
        run_cwd = None
    else:
        # Resolve relative to agent dir: ../app -> APP_ROOT
        run_cwd = (AGENT_DIR / cwd).resolve()
        if not run_cwd.is_dir():
            return f"Error: cwd is not a directory: {run_cwd}"
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


def read_file(path: str) -> str:
    """Read a file from ../app. Path is relative to the app root."""
    try:
        full = _resolve_app_path(path)
        return full.read_text(encoding="utf-8", errors="replace")
    except ValueError as e:
        return str(e)
    except FileNotFoundError:
        return f"Error: file not found: {path}"
    except IsADirectoryError:
        return f"Error: path is a directory, not a file: {path}"
    except Exception as e:
        return f"Error reading file: {e}"


def write_file(path: str, contents: str) -> str:
    """Write contents to a file in ../app. Path is relative to the app root. Creates parent dirs if needed."""
    try:
        full = _resolve_app_path(path)
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(contents, encoding="utf-8")
        return f"Wrote {path}"
    except ValueError as e:
        return str(e)
    except Exception as e:
        return f"Error writing file: {e}"
