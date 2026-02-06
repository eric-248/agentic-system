"""Aggregate trial results into task-level and suite-level metrics."""

from .types import SuiteResult, TaskResult, TrialResult


def aggregate_task(task_id: str, trials: list[TrialResult]) -> TaskResult:
    """Aggregate trials for a single task."""
    if not trials:
        return TaskResult(
            task_id=task_id,
            trials=[],
            pass_rate=0.0,
            mean_turns=0.0,
            mean_tool_calls=0.0,
            mean_tokens=0.0,
            mean_latency_sec=0.0,
        )

    n = len(trials)
    passed = sum(1 for t in trials if all(gr.passed for gr in t.grader_results))
    pass_rate = passed / n if n else 0.0
    mean_turns = sum(t.trajectory.n_turns for t in trials) / n
    mean_tool_calls = sum(t.trajectory.n_tool_calls for t in trials) / n
    mean_tokens = sum(t.trajectory.usage.get("total_tokens", 0) for t in trials) / n
    mean_latency_sec = sum(t.trajectory.latency_sec for t in trials) / n

    return TaskResult(
        task_id=task_id,
        trials=trials,
        pass_rate=pass_rate,
        mean_turns=mean_turns,
        mean_tool_calls=mean_tool_calls,
        mean_tokens=mean_tokens,
        mean_latency_sec=mean_latency_sec,
    )


def aggregate_suite(suite_id: str, task_results: list[TaskResult]) -> SuiteResult:
    """Aggregate task results for a suite."""
    if not task_results:
        return SuiteResult(suite_id=suite_id, task_results=[], overall_pass_rate=0.0)

    total_trials = sum(len(tr.trials) for tr in task_results)
    total_passed = sum(
        sum(1 for t in tr.trials if all(gr.passed for gr in t.grader_results))
        for tr in task_results
    )
    overall_pass_rate = total_passed / total_trials if total_trials else 0.0

    return SuiteResult(
        suite_id=suite_id,
        task_results=task_results,
        overall_pass_rate=overall_pass_rate,
    )
