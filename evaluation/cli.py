"""CLI for running evaluations."""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Ensure project root on path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from evaluation.aggregate import aggregate_suite, aggregate_task
from evaluation.config import (
    DEFAULT_MAX_TURNS,
    DEFAULT_MODEL,
    DEFAULT_TIMEOUT_SEC,
    DEFAULT_TRIALS_PER_TASK,
    RESULTS_DIR,
)
from evaluation.loader import load_suite
from evaluation.runner import run_task


def main():
    #parse args
    parser = argparse.ArgumentParser(description="Run evaluation suite")
    parser.add_argument("--suite", "-s", default="coding", help="Suite id (default: coding)")
    parser.add_argument("--trials", "-n", type=int, default=DEFAULT_TRIALS_PER_TASK, help="Trials per task")
    parser.add_argument("--output", "-o", type=Path, default=RESULTS_DIR, help="Output directory")
    parser.add_argument("--max-turns", type=int, default=DEFAULT_MAX_TURNS, help="Max agent turns per trial")
    parser.add_argument("--model", "-m", default=DEFAULT_MODEL, help="Model name")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SEC, help="Timeout per trial (seconds)")
    args = parser.parse_args()

    #load the suite
    suite_id, tasks = load_suite(args.suite)

    #create the output directory
    run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.output) / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Suite: {suite_id} ({len(tasks)} tasks)")
    print(f"Trials per task: {args.trials}")
    print(f"Output: {out_dir}")
    print()

    task_results = []
    for task in tasks:
        print(f"Running task: {task.id} ({task.name})")
        trials = run_task(
            task,
            n_trials=args.trials,
            model=args.model,
            max_turns=args.max_turns,
            timeout_sec=args.timeout,
        )

        #save the results of the trial
        task_out = out_dir / task.id
        task_out.mkdir(parents=True, exist_ok=True)
        for i, tr in enumerate(trials):
            trial_dir = task_out / f"trial_{i}"
            trial_dir.mkdir(parents=True, exist_ok=True)
            (trial_dir / "trajectory.json").write_text(
                json.dumps(
                    {
                        "messages": tr.trajectory.messages,
                        "n_turns": tr.trajectory.n_turns,
                        "n_tool_calls": tr.trajectory.n_tool_calls,
                        "usage": tr.trajectory.usage,
                        "latency_sec": tr.trajectory.latency_sec,
                        "finished": tr.trajectory.finished,
                    },
                    indent=2,
                )
            )
            (trial_dir / "outcome.json").write_text(
                json.dumps(
                    {
                        "pytest_exit_code": tr.outcome.pytest_exit_code,
                        "pytest_stdout": tr.outcome.pytest_stdout,
                        "pytest_stderr": tr.outcome.pytest_stderr,
                        "db_todos": tr.outcome.db_todos,
                    },
                    indent=2,
                )
            )
            (trial_dir / "grader_results.json").write_text(
                json.dumps(
                    [
                        {"grader_name": gr.grader_name, "passed": gr.passed, "score": gr.score, "details": gr.details}
                        for gr in tr.grader_results
                    ],
                    indent=2,
                )
            )

        #aggregate the results of the trial
        tr_agg = aggregate_task(task.id, trials)
        task_results.append(tr_agg)
        print(f" {tr_agg.pass_rate:.0%} passed, mean turns={tr_agg.mean_turns:.1f}, mean latency={tr_agg.mean_latency_sec:.1f}s")

    #aggregate the results of the suite
    suite_result = aggregate_suite(suite_id, task_results)

    summary = {
        "suite_id": suite_id,
        "run_id": run_id,
        "overall_pass_rate": suite_result.overall_pass_rate,
        "tasks": [
            {
                "task_id": tr.task_id,
                "pass_rate": tr.pass_rate,
                "mean_turns": tr.mean_turns,
                "mean_tool_calls": tr.mean_tool_calls,
                "mean_tokens": tr.mean_tokens,
                "mean_latency_sec": tr.mean_latency_sec,
            }
            for tr in task_results
        ],
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))

    print()
    print(f"Overall pass rate: {suite_result.overall_pass_rate:.1%}")
    print(f"Summary: {out_dir / 'summary.json'}")
    return 0 if suite_result.overall_pass_rate >= 1.0 else 1


if __name__ == "__main__":
    sys.exit(main())
