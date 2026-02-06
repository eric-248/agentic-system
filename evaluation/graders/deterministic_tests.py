"""Grader: pass if pytest exits with 0."""

from ..types import GraderResult, Outcome, Task, Trajectory


def grade(*, trajectory: Trajectory, outcome: Outcome, task: Task) -> GraderResult:
    """Pass if pytest_exit_code == 0."""
    passed = outcome.pytest_exit_code == 0
    return GraderResult(
        grader_name="deterministic_tests",
        passed=passed,
        score=1.0 if passed else 0.0,
        details={"pytest_exit_code": outcome.pytest_exit_code},
    )
