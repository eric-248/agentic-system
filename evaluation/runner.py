"""Run tasks: create app copy, run agent, capture outcome, run graders."""

import shutil
import sys
import tempfile
from pathlib import Path

from .config import APP_DIR, DEFAULT_MAX_TURNS, DEFAULT_MODEL, DEFAULT_TIMEOUT_SEC
from .outcome import capture_outcome
from .types import GraderResult, Outcome, Task, Trajectory, TrialResult

# Ensure project root is on path so we can import agent
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from agent.main import run_agent_task  # noqa: E402


def _get_grader(name: str):
    """Load grader by name."""
    from .graders import deterministic_tests, state_check, tool_calls

    graders = {
        "deterministic_tests": deterministic_tests,
        "state_check": state_check,
        "tool_calls": tool_calls,
    }
    return graders.get(name)


def run_trial(
    task: Task,
    trial_index: int,
    *,
    app_baseline: Path | None = None,
    model: str = DEFAULT_MODEL,
    max_turns: int = DEFAULT_MAX_TURNS,
    timeout_sec: float | None = DEFAULT_TIMEOUT_SEC,
) -> TrialResult:
    """Run a single trial: copy app, run agent, capture outcome, run graders."""
    baseline = app_baseline or APP_DIR
    with tempfile.TemporaryDirectory(prefix="eval_trial_") as tmp:
        trial_app = Path(tmp) / "app"
        shutil.copytree(baseline, trial_app)
        # Install deps in the copy so poetry run pytest works
        import subprocess

        subprocess.run(
            ["poetry", "install", "--no-interaction"],
            cwd=trial_app,
            capture_output=True,
            timeout=60,
        )

        system_prompt = task.system_prompt_override or (
            "You are an expert coding agent. The app is in ../app. "
            "When running tests or server commands, ALWAYS prepend poetry run (e.g. poetry run pytest)."
        )

        result = run_agent_task(
            task.instruction,
            app_root=trial_app,
            system_prompt=system_prompt,
            model=model,
            max_turns=max_turns,
            timeout_sec=timeout_sec,
        )

        trajectory = Trajectory(
            messages=result.messages,
            n_turns=result.n_turns,
            n_tool_calls=result.n_tool_calls,
            usage=result.usage,
            latency_sec=result.latency_sec,
            finished=result.finished,
        )

        outcome = capture_outcome(trial_app)

        grader_results: list[GraderResult] = []
        for grader_name in task.graders:
            grader_fn = _get_grader(grader_name)
            if grader_fn:
                gr = grader_fn(trajectory=trajectory, outcome=outcome, task=task)
                grader_results.append(gr)

        return TrialResult(
            task_id=task.id,
            trial_index=trial_index,
            trajectory=trajectory,
            outcome=outcome,
            grader_results=grader_results,
        )


def run_task(
    task: Task,
    n_trials: int = 3,
    *,
    model: str = DEFAULT_MODEL,
    max_turns: int = DEFAULT_MAX_TURNS,
    timeout_sec: float | None = DEFAULT_TIMEOUT_SEC,
) -> list[TrialResult]:
    """Run a task N times and return trial results."""
    results = []
    for i in range(n_trials):
        tr = run_trial(task, i, model=model, max_turns=max_turns, timeout_sec=timeout_sec)
        results.append(tr)
    return results
