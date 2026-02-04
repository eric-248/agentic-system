# basic coding agent

This repository is designed to mimic a basic coding agent.

## Architecture

The project is structured as a monorepo with two components:

* **`/app` (The Target):** FastAPI backend with a SQLite database and test suite. It serves as the ground truth for evaluating agent performance.
* **`/agent` (The Actor):** Agent harness. It uses an LLM (OpenAI/Anthropic) and a set of file-system and terminal tools to modify the `/app` code and run its tests.

## Getting Started

### Prerequisites

* Python 3.10+
* [Poetry](https://python-poetry.org/) (Dependency Management)
* OpenAI API Key

### 1. Setup the Target App

The app for now is just purely a codebase for the agent to interact with.

But if one were to want to startup the app

```bash
cd app
poetry install

# Verify the app works
poetry run python -m pytest

#Startup the app
poetry run python -m uvicorn main:app --reload

```

### 2. Setup the Agent

The Agent requires access to the LLM and the tools.

```bash
cd agent
poetry install

# Configure Environment
# Add your OPENAI_API_KEY=... to the .env file

```

---

## How to Run

### Manual Agent Loop

Run the agent interface to give it commands against the app.

```bash
cd agent
poetry run python main.py

#If you get stuck in a quote prompt that looks like this
<quote>
<quote>

Exit using Ctrl+C

```

**Example Prompts:**

> "Add a new field 'priority' to the Todo model and update the database schema."
> "There is a bug where creating a todo with an empty title succeeds. Fix it."
> "Run the tests and fix any failures."

### Resetting the State

Since the Agent modifies the actual code in `/app`, you need a way to reset the experiment. Use Git for this.

```bash
# From the root directory
git restore app/

```

---

## Structure

```text
Agentic/
├── .gitignore          # Global ignores (API keys, DBs)
├── README.md           # This file
├── app/                # The Target Application
│   ├── main.py         # FastAPI Endpoints
│   ├── models.py       # SQLModel/Pydantic Definitions
│   ├── database.py     # DB Connection
│   ├── tests/          # Pytest Suite
│   └── poetry.lock     # Locked dependencies
└── agent/              # The Agent Harness
    ├── main.py         # ReAct Loop / Logic
    ├── tools.py        # File/Terminal Interaction Tools
    └── .env            # API Keys (Not committed)

```

