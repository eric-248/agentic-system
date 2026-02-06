"""Core types for the evaluation harness."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Task:
    """A single evaluation task: inputs + success criteria + graders."""

    id: str
    name: str
    instruction: str
    system_prompt_override: str | None = None
    graders: list[str] = field(default_factory=lambda: ["deterministic_tests"])
    state_check: dict[str, Any] | None = None
    tool_calls: dict[str, Any] | None = None


@dataclass
class Trajectory:
    """Transcript for a trial: messages + metadata."""

    messages: list[dict[str, Any]]
    n_turns: int
    n_tool_calls: int
    usage: dict[str, int]
    latency_sec: float
    finished: bool


@dataclass
class Outcome:
    """Final environment state at end of a trial."""

    pytest_exit_code: int
    pytest_stdout: str
    pytest_stderr: str
    db_todos: list[dict[str, Any]] | None = None
    files_changed: list[str] | None = None


@dataclass
class GraderResult:
    """Result from a single grader."""

    grader_name: str
    passed: bool
    score: float
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class TrialResult:
    """Result of one trial: trajectory + outcome + grader results."""

    task_id: str
    trial_index: int
    trajectory: Trajectory
    outcome: Outcome
    grader_results: list[GraderResult]


@dataclass
class TaskResult:
    """Aggregated result for a task across all trials."""

    task_id: str
    trials: list[TrialResult]
    pass_rate: float
    mean_turns: float
    mean_tool_calls: float
    mean_tokens: float
    mean_latency_sec: float


@dataclass
class SuiteResult:
    """Aggregated result for an evaluation suite."""

    suite_id: str
    task_results: list[TaskResult]
    overall_pass_rate: float
