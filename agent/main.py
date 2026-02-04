"""ReAct loop: user input -> LLM -> parse tool calls -> execute tools -> send results back -> repeat."""

import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from tools import read_file, run_command, write_file

load_dotenv()
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise SystemExit("Missing OPENAI_API_KEY.")

SYSTEM_PROMPT = (
    "You are an expert coding agent. The app is in ../app. "
    "When running tests or server commands, ALWAYS prepend poetry run (e.g. poetry run pytest)."
)

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


def run_tool(name: str, arguments: dict) -> str:
    """Execute a tool by name with the given arguments; return result string."""
    fn = TOOL_FUNCTIONS.get(name)
    if not fn:
        return f"Unknown tool: {name}"
    try:
        return str(fn(**arguments))
    except TypeError as e:
        return f"Tool argument error: {e}"
    except Exception as e:
        return f"Tool error: {e}"


def main() -> None:
    client = OpenAI(api_key=api_key)
    user_input = input("You: ").strip()
    if not user_input:
        return
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ]
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
        break


if __name__ == "__main__":
    main()
