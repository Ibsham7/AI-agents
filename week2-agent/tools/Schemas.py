# tools/schemas.py
from typing import Any

CODE_REVIEW_TOOLS : list[Any] = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": (
                "Read the contents of a Python source file. Use this to inspect "
                "code before reviewing it. Always read a file before making claims about it."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Relative path to the file"}
                },
                "required": ["filepath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List files in a directory to understand the project structure.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dirpath": {"type": "string"}
                },
                "required": ["dirpath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_linter",
            "description": (
                "Run pyflakes static analysis on a Python file. Returns undefined names, "
                "unused imports, and other static errors. Always run this before manual review."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string"}
                },
                "required": ["filepath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_complexity",
            "description": (
                "Measure cyclomatic complexity of functions in a Python file. "
                "A score above 10 means a function is too complex and should be refactored."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string"}
                },
                "required": ["filepath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_code",
            "description": (
                "Execute a Python code snippet and see the output. Use this to: "
                "verify a bug exists by reproducing it, test a proposed fix, or "
                "write and run a quick unit test. "
                "Do NOT use to run the target file directly — write targeted test snippets."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code to execute. Must be self-contained."
                    }
                },
                "required": ["code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write the final review report to outputs/reviews/<filename>.md",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string"},
                    "content": {"type": "string"}
                },
                "required": ["filepath", "content"]
            }
        }
    }
]