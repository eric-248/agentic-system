"""Allow running evaluation as python -m evaluation."""

import sys

from evaluation.cli import main

if __name__ == "__main__":
    sys.exit(main())
