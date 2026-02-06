"""Shared configuration for the evaluation harness."""

from pathlib import Path

# Paths relative to evaluation/ directory
EVALUATION_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = EVALUATION_DIR.parent
APP_DIR = PROJECT_ROOT / "app"
AGENT_DIR = PROJECT_ROOT / "agent"

# Default run configuration
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_MAX_TURNS = 50
DEFAULT_TIMEOUT_SEC = 600.0
DEFAULT_TRIALS_PER_TASK = 3
DEFAULT_CONCURRENCY = 1

# Results output
RESULTS_DIR = EVALUATION_DIR / "results"
SUITES_DIR = EVALUATION_DIR / "suites"
