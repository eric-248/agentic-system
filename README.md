# Agentic System Evaluation Sandbox

This repository is a dual-environment sandbox designed to study, build, and evaluate AI Coding Agents. It separates the "Actor" (The Agent) from the "Environment" (The App) to create a clean, deterministic testing ground for AI capabilities.

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

The App must be running or installable for the agent to interact with it.

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
cp .env.example .env  # (Or create .env manually)
# Add your OPENAI_API_KEY=... to the .env file

```

---

## How to Run

### Manual Agent Loop

Run the agent interface to give it commands against the app.

```bash
cd agent
poetry run python main.py

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

## Evaluation Goals

This project serves as the foundation for building an **AI Evaluation Tool**. The current phase focuses on:

1. **Tool Use Accuracy:** Can the agent correctly invoke `pytest` using `poetry run`?
2. **Error Recovery:** If a test fails, can the agent read the traceback and fix the code?
3. **State Management:** Does the agent understand that modifying a Model requires updating the Pydantic schema?

## Project Structure

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

