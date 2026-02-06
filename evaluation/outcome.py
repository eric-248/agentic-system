"""Capture outcome: final state of the environment after a trial."""

import sqlite3
import subprocess
from pathlib import Path

from .types import Outcome


def capture_outcome(app_root: Path) -> Outcome:
    """Run pytest in the app copy and optionally capture DB state. Returns Outcome."""
    pytest_result = subprocess.run(
        ["poetry", "run", "pytest", "-v"],
        cwd=app_root,
        capture_output=True,
        text=True,
        timeout=120,
    )

    db_todos: list[dict] | None = None
    db_path = app_root / "todo.db"
    if db_path.exists():
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.execute("SELECT id, title, description, completed FROM todos")
            rows = cur.fetchall()
            db_todos = [dict(row) for row in rows]
            conn.close()
        except Exception:
            pass

    return Outcome(
        pytest_exit_code=pytest_result.returncode,
        pytest_stdout=pytest_result.stdout or "",
        pytest_stderr=pytest_result.stderr or "",
        db_todos=db_todos,
    )
