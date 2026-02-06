"""Grader: assertions on outcome state (e.g. DB snapshot)."""

from ..types import GraderResult, Outcome, Task, Trajectory


def grade(*, trajectory: Trajectory, outcome: Outcome, task: Task) -> GraderResult:
    details = {}
    passed = True

    if "no_empty_titles" in task.state_check:
        todos = outcome.db_todos or []
        empty = [t for t in todos if t.get("title") == "" or t.get("title") is None]
        ok = len(empty) == 0
        details["no_empty_titles"] = ok
        if not ok:
            passed = False

    if "min_todos" in task.state_check:
        n = task.state_check["min_todos"]
        todos = outcome.db_todos or []
        ok = len(todos) >= n
        details["min_todos"] = {"expected": n, "actual": len(todos)}
        if not ok:
            passed = False

    if "max_todos" in task.state_check:
        n = task.state_check["max_todos"]
        todos = outcome.db_todos or []
        ok = len(todos) <= n
        details["max_todos"] = {"expected": n, "actual": len(todos)}
        if not ok:
            passed = False

    return GraderResult(
        grader_name="state_check",
        passed=passed,
        score=1.0 if passed else 0.0,
        details=details,
    )
