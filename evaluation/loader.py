"""Load evaluation suites and tasks from YAML."""

import yaml
from pathlib import Path

from .config import SUITES_DIR
from .types import Task


def load_suite(suite_id: str) -> tuple[str, list[Task]]:
    """Load a suite by id. Returns (suite_id, list of Task)."""
    path = SUITES_DIR / f"{suite_id}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Suite not found: {path}")

    data = yaml.safe_load(path.read_text())
    suite_id = data.get("suite_id", suite_id)
    tasks_data = data.get("tasks", [])

    tasks = []
    for t in tasks_data:
        tasks.append(
            Task(
                id=t["id"],
                name=t["name"],
                instruction=t["instruction"].strip() if isinstance(t["instruction"], str) else str(t["instruction"]),
                system_prompt_override=t.get("system_prompt_override"),
                graders=t.get("graders", ["deterministic_tests"]),
                state_check=t.get("state_check"),
                tool_calls=t.get("tool_calls"),
            )
        )
    return suite_id, tasks
