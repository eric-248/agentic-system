"""ReAct loop: user input -> LLM -> parse tool calls -> execute tools -> send results back -> repeat."""

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from tools import APP_ROOT, get_tool_functions, read_file, run_command, write_file

load_dotenv()
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise SystemExit("Missing OPENAI_API_KEY.")

SYSTEM_PROMPT = (
    "You are an expert coding agent. The app is in ../app. "
    "When running tests or server commands, ALWAYS prepend poetry run (e.g. poetry run pytest)."
)


@dataclass
class RunResult:
    """Result of running an agent task programmatically."""

    messages: list[dict[str, Any]]
    n_turns: int
    n_tool_calls: int
    usage: dict[str, int]
    latency_sec: float
    finished: bool


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run a shell command. Use cwd='../app' to run from the app directory (e.g. for poetry run pytest).",
            "parameters": {
                "type": "object",
                "properties": {
                    "cmd": {"type": "string", "description": "The shell command to run."},
                    "cwd": {
                        "type": "string",
                        "description": "Optional working directory, e.g. '../app' to run from the app root.",
                    },
                },
                "required": ["cmd"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file from ../app. Path is relative to the app root.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path relative to app root, e.g. 'main.py' or 'tests/test_main.py'."},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write contents to a file in ../app. Path is relative to the app root. Creates parent dirs if needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path relative to app root."},
                    "contents": {"type": "string", "description": "File contents to write."},
                },
                "required": ["path", "contents"],
            },
        },
    },
]

TOOL_FUNCTIONS = {
    "run_command": run_command,
    "read_file": read_file,
    "write_file": write_file,
}


def _run_tool(name: str, arguments: dict, tool_functions: dict[str, callable]) -> str:
    """Execute a tool by name with the given arguments; return result string."""
    fn = tool_functions.get(name)
    if not fn:
        return f"Unknown tool: {name}"
    try:
        return str(fn(**arguments))
    except TypeError as e:
        return f"Tool argument error: {e}"
    except Exception as e:
        return f"Tool error: {e}"


def run_tool(name: str, arguments: dict) -> str:
    """Execute a tool by name with the given arguments; return result string. Uses default TOOL_FUNCTIONS."""
    return _run_tool(name, arguments, TOOL_FUNCTIONS)


def run_agent_task(
    task_instruction: str,
    *,
    app_root: Path,
    system_prompt: str = SYSTEM_PROMPT,
    model: str = "gpt-4o-mini",
    max_turns: int = 50,
    timeout_sec: float | None = None,
) -> RunResult:
    """Run the agent on a single task and return transcript + metadata.

    Uses tools bound to app_root so the evaluator can run trials against isolated app copies.
    """
    client = OpenAI(api_key=api_key)
    tool_functions = get_tool_functions(app_root)

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": task_instruction},
    ]

    n_turns = 0
    n_tool_calls = 0
    usage: dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    start = time.perf_counter()
    finished = False

    while n_turns < max_turns:
        if timeout_sec is not None and (time.perf_counter() - start) > timeout_sec:
            break

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS,
        )
        msg = response.choices[0].message

        if response.usage:
            usage["prompt_tokens"] = getattr(response.usage, "prompt_tokens", 0) or 0
            usage["completion_tokens"] = getattr(response.usage, "completion_tokens", 0) or 0
            usage["total_tokens"] = getattr(response.usage, "total_tokens", 0) or 0

        if msg.tool_calls:
            n_turns += 1
            messages.append(
                {
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                        }
                        for tc in msg.tool_calls
                    ],
                }
            )
            for tc in msg.tool_calls:
                n_tool_calls += 1
                name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                except json.JSONDecodeError:
                    args = {}
                result = _run_tool(name, args, tool_functions)
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
            continue

        if msg.content:
            n_turns += 1

        messages.append({"role": "assistant", "content": msg.content or ""})
        finished = True
        break

    latency_sec = time.perf_counter() - start
    return RunResult(
        messages=messages,
        n_turns=n_turns,
        n_tool_calls=n_tool_calls,
        usage=usage,
        latency_sec=latency_sec,
        finished=finished,
    )


def main() -> None:
    client = OpenAI(api_key=api_key)
    print("Agent ready. Type your message (or 'exit' to quit).")
    messages = []
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("exit", "quit"):
            break
        if not user_input:
            continue
        if not messages:
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input},
            ]
        else:
            messages.append({"role": "user", "content": user_input})
        while True:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=TOOLS,
            )
            msg = response.choices[0].message
            if msg.tool_calls:
                messages.append(
                    {
                        "role": "assistant",
                        "content": msg.content or "",
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                            }
                            for tc in msg.tool_calls
                        ],
                    }
                )
                for tc in msg.tool_calls:
                    name = tc.function.name
                    try:
                        args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                    except json.JSONDecodeError:
                        args = {}
                    result = run_tool(name, args)
                    messages.append(
                        {"role": "tool", "tool_call_id": tc.id, "content": result}
                    )
                continue
            if msg.content:
                print(msg.content)
            messages.append({"role": "assistant", "content": msg.content or ""})
            break


if __name__ == "__main__":
    main()
