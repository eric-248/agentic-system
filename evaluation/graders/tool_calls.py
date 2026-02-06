"""Grader: efficiency constraints on tool calls and turns."""

from ..types import GraderResult, Outcome, Task, Trajectory


def grade(*, trajectory: Trajectory, outcome: Outcome, task: Task) -> GraderResult:
    """Check tool/turn limits from task.tool_calls."""
    details = {
        "n_turns": trajectory.n_turns,
        "n_tool_calls": trajectory.n_tool_calls,
    }
    passed = True

    max_turns = task.tool_calls.get("max_turns")
    if max_turns is not None and trajectory.n_turns > max_turns:
        details["max_turns"] = {"limit": max_turns, "actual": trajectory.n_turns}
        passed = False

    max_tool_calls = task.tool_calls.get("max_tool_calls")
    if max_tool_calls is not None and trajectory.n_tool_calls > max_tool_calls:
        details["max_tool_calls"] = {"limit": max_tool_calls, "actual": trajectory.n_tool_calls}
        passed = False

    return GraderResult(
        grader_name="tool_calls",
        passed=passed,
        score=1.0 if passed else 0.0,
        details=details,
    )
