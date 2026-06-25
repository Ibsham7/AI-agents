# Week 2 — Code-Execution Agents & Sandboxing
### Detailed Daily Workflow | Intensive Track (20+ hrs/week)

---

## What You Will Have Built by End of Week 2

Two fully working agents — back to back, 3–4 days each:

**Agent 1 — Code Review Agent:** point it at a Python file or small repo, it reads the code, reasons about bugs / security issues / style violations, writes and runs a targeted test to verify each issue it found, and produces a structured review report with fix suggestions.

**Agent 2 — Data Analyst Agent:** give it a CSV, ask questions in plain English. It writes pandas code, executes it, sees the result, and either answers you or iterates on the code if something went wrong. Variables persist across turns so you can have a real multi-turn data conversation.

The new skill this week is treating **code execution as a tool** — and everything that comes with that: sandboxing, error-as-observation loops, code repair, and the persistent execution state problem.

---

## How Week 2 Connects to Week 1

The agent loop you built in Week 1 (send → `finish_reason == "tool_calls"` → execute → append result → repeat) does not change. What changes is what the tool *does*. Last week tools were stateless lookups (search, calculate). This week, tools have **side effects** — they write files, run processes, mutate state. That changes how you design them, handle errors, and think about safety.

Week 1 mental model: tool = function that returns information.
Week 2 mental model: tool = function that *does something* and returns what happened.

---

## Before Day 1 — Setup (1–2 hrs)

### No new API keys needed
You already have OpenRouter, Tavily, Serper from Week 1. Week 2 adds zero new external services — the code executor runs entirely locally.

### New packages
```bash
pip install pandas matplotlib seaborn tabulate pytest radon pyflakes
```

| Package | Used for |
|---|---|
| `pandas` | DataFrame operations in the data analyst agent |
| `matplotlib` / `seaborn` | Chart generation |
| `tabulate` | Pretty-print DataFrame results as text for the model to read |
| `pytest` | Code Review Agent runs tests in a subprocess |
| `radon` | Cyclomatic complexity scoring in code review |
| `pyflakes` | Static analysis tool the agent can call |

### Project structure (extends Week 1)
```
week2-agent/
├── .env
├── sandbox/
│   ├── __init__.py
│   ├── executor.py          # Safe subprocess-based code runner
│   └── namespace.py         # Persistent exec() namespace for data analyst
├── agents/
│   ├── __init__.py
│   ├── code_review.py       # Code Review Agent
│   └── data_analyst.py      # Data Analyst Agent
├── tools/
│   ├── __init__.py
│   ├── file_tools.py        # read_file, write_file, list_directory
│   ├── execution_tools.py   # execute_python, run_tests, run_linter
│   └── analysis_tools.py    # describe_dataframe, get_column_info
├── test_targets/            # Intentionally buggy Python files to review
│   ├── buggy_api.py
│   ├── insecure_auth.py
│   └── inefficient_sort.py
├── datasets/                # CSVs for the data analyst
│   ├── sales.csv
│   └── students.csv
└── outputs/
    ├── reviews/
    └── charts/
```

---

## The Core New Concept: Code Execution as a Tool

Before writing any agent, build the executor in isolation and understand its failure modes. This is the most important piece of infrastructure this week.

### Why subprocess instead of eval() or exec()

You used `eval()` for the calculator in Week 1, which was fine for arithmetic. You cannot use bare `eval()` or `exec()` for arbitrary code because:

- `eval("__import__('os').system('rm -rf /')")` — yes, this works
- No timeout means an infinite loop hangs your entire program
- No output capture means you can't feed results back to the model
- Exceptions crash your agent loop rather than being returned as tool feedback

`subprocess` gives you: process isolation, timeout enforcement, stdout/stderr capture, and a clean exit even when the executed code crashes.

### Two execution strategies — know when to use each

**Strategy A — Subprocess (for Code Review Agent):** each execution is completely isolated. Fresh Python process, clean environment, no state between calls. Safe, predictable, good when you don't need variables to persist.

**Strategy B — Persistent namespace via exec() (for Data Analyst Agent):** a single shared dict acts as a fake "session." Variables defined in one call are available in the next. Faster and stateful, but less isolated. Acceptable for local dev tools where you control the input.

---

## Day 1 — Build the Sandbox (4 hrs)

**Goal:** a robust code executor that your agents will rely on all week. Get this right before touching agents.

### The subprocess executor

```python
# sandbox/executor.py
import subprocess
import sys
import tempfile
import os
import textwrap
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

@dataclass
class ExecutionResult:
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool
    
    @property
    def success(self) -> bool:
        return self.exit_code == 0 and not self.timed_out
    
    def to_tool_string(self) -> str:
        """Format result for the model to read."""
        if self.timed_out:
            return "EXECUTION TIMED OUT after 10 seconds. The code may contain an infinite loop."
        
        parts = []
        if self.stdout.strip():
            parts.append(f"STDOUT:\n{self.stdout.strip()}")
        if self.stderr.strip():
            parts.append(f"STDERR:\n{self.stderr.strip()}")
        if not parts:
            parts.append("(no output)")
        
        status = "SUCCESS" if self.success else f"FAILED (exit code {self.exit_code})"
        return f"[{status}]\n" + "\n\n".join(parts)


# Imports the agent's generated code is NOT allowed to use
BLOCKED_IMPORTS = {
    "subprocess", "multiprocessing", "socket", "urllib",
    "httpx", "requests", "shutil",  # no network, no filesystem wipe
}

def _check_for_blocked_imports(code: str) -> Optional[str]:
    """Quick static check before even running the code."""
    for blocked in BLOCKED_IMPORTS:
        if f"import {blocked}" in code or f"from {blocked}" in code:
            return f"Blocked: code attempts to import '{blocked}', which is not allowed."
    return None


def execute_python(code: str, timeout: int = 10) -> ExecutionResult:
    """
    Run arbitrary Python code in an isolated subprocess.
    Returns stdout, stderr, exit code, and whether it timed out.
    """
    # Static check first — don't even spawn a process for obvious violations
    block_reason = _check_for_blocked_imports(code)
    if block_reason:
        return ExecutionResult(
            stdout="", stderr=block_reason, exit_code=1, timed_out=False
        )
    
    # Write code to a temp file (handles multiline, indentation, quotes)
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write(code)
        temp_path = f.name
    
    try:
        result = subprocess.run(
            [sys.executable, temp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            # Restrict environment — no inheriting parent env vars unnecessarily
            env={
                "PATH": os.environ.get("PATH", ""),
                "PYTHONPATH": os.environ.get("PYTHONPATH", ""),
            }
        )
        return ExecutionResult(
            stdout=result.stdout[:5000],   # cap output — don't flood context
            stderr=result.stderr[:2000],
            exit_code=result.returncode,
            timed_out=False
        )
    except subprocess.TimeoutExpired:
        return ExecutionResult(
            stdout="", stderr="", exit_code=-1, timed_out=True
        )
    finally:
        os.unlink(temp_path)  # always clean up
```

### Test the executor before touching agents

```python
# test the executor directly — don't skip this
from sandbox.executor import execute_python

tests = [
    # Basic success
    ("print('hello world')", True),
    # Arithmetic
    ("x = 10 * 3.14\nprint(f'{x:.2f}')", True),
    # Runtime error — should return cleanly, not crash your program
    ("print(1 / 0)", False),
    # Timeout — should not hang
    ("while True: pass", False),
    # Blocked import — should be caught statically
    ("import subprocess\nsubprocess.run(['ls'])", False),
    # Multi-line with state
    ("data = [1, 2, 3, 4, 5]\nprint(sum(data) / len(data))", True),
]

for code, expected_success in tests:
    result = execute_python(code)
    status = "✅" if result.success == expected_success else "❌ UNEXPECTED"
    print(f"{status} | success={result.success}")
    print(f"   → {result.to_tool_string()[:100]}\n")
```

**All six must pass before moving on.** If the timeout test hangs, your timeout logic is broken.

### The persistent namespace executor (for the Data Analyst)

```python
# sandbox/namespace.py
import io
import sys
import traceback
from contextlib import redirect_stdout, redirect_stderr
from dataclasses import dataclass, field
from typing import Any

@dataclass
class NamespaceResult:
    stdout: str
    error: str
    success: bool
    local_vars: dict = field(default_factory=dict)
    
    def to_tool_string(self) -> str:
        parts = []
        if self.stdout.strip():
            parts.append(f"OUTPUT:\n{self.stdout.strip()}")
        if self.error:
            parts.append(f"ERROR:\n{self.error}")
        if not parts:
            parts.append("(code executed, no output)")
        return "\n\n".join(parts)


class PersistentNamespace:
    """
    Shared execution environment — variables survive between exec() calls.
    This is the 'session' for a data analysis conversation.
    """
    def __init__(self):
        # Pre-import safe libraries so the agent can use them without importing
        import pandas as pd
        import matplotlib
        matplotlib.use("Agg")  # non-interactive backend — no GUI popups
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        self._namespace: dict[str, Any] = {
            "pd": pd,
            "plt": plt,
            "sns": sns,
            "__builtins__": __builtins__,
        }
    
    def execute(self, code: str) -> NamespaceResult:
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        
        try:
            with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
                exec(code, self._namespace)
            
            return NamespaceResult(
                stdout=stdout_buf.getvalue()[:4000],
                error="",
                success=True,
                local_vars={
                    k: type(v).__name__
                    for k, v in self._namespace.items()
                    if not k.startswith("_") and k not in ("pd", "plt", "sns")
                }
            )
        except Exception:
            return NamespaceResult(
                stdout=stdout_buf.getvalue(),
                error=traceback.format_exc(),
                success=False
            )
    
    def get_defined_vars(self) -> list[str]:
        """Tell the model what variables are already in scope."""
        return [
            k for k in self._namespace
            if not k.startswith("_") and k not in ("pd", "plt", "sns")
        ]
    
    def reset(self):
        """Clear all user-defined variables but keep the imports."""
        self.__init__()
```

---

## Day 2 — File Tools + Tool Definitions (3 hrs)

**Goal:** build the file-reading and linting tools the Code Review Agent needs, and define all tool schemas.

```python
# tools/file_tools.py
import os
from pathlib import Path

# Safety: agents can only read from these directories
ALLOWED_READ_DIRS = [
    Path("test_targets").resolve(),
    Path("datasets").resolve(),
    Path("outputs").resolve(),
]

def _is_allowed_path(path: Path) -> bool:
    path = path.resolve()
    return any(
        str(path).startswith(str(allowed))
        for allowed in ALLOWED_READ_DIRS
    )

def read_file(filepath: str) -> str:
    path = Path(filepath)
    if not path.exists():
        return f"Error: file '{filepath}' does not exist."
    if not _is_allowed_path(path):
        return f"Error: reading outside allowed directories is not permitted."
    if path.stat().st_size > 100_000:  # 100KB cap
        return f"Error: file too large ({path.stat().st_size} bytes). Read in chunks."
    return path.read_text(encoding="utf-8")

def list_directory(dirpath: str) -> str:
    path = Path(dirpath)
    if not path.is_dir():
        return f"Error: '{dirpath}' is not a directory."
    entries = []
    for item in sorted(path.iterdir()):
        kind = "DIR" if item.is_dir() else "FILE"
        size = "" if item.is_dir() else f"({item.stat().st_size} bytes)"
        entries.append(f"  {kind}  {item.name} {size}")
    return f"Contents of {dirpath}:\n" + "\n".join(entries)

def write_file(filepath: str, content: str) -> str:
    """Only writes to outputs/ directory."""
    path = Path(filepath)
    if not str(path.resolve()).startswith(str(Path("outputs").resolve())):
        return "Error: can only write to the outputs/ directory."
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"Written {len(content)} characters to {filepath}"
```

```python
# tools/execution_tools.py
import subprocess, sys, tempfile, os
from sandbox.executor import execute_python, ExecutionResult

def run_linter(filepath: str) -> str:
    """Run pyflakes static analysis on a file."""
    result = subprocess.run(
        [sys.executable, "-m", "pyflakes", filepath],
        capture_output=True, text=True
    )
    output = result.stdout + result.stderr
    return output.strip() if output.strip() else "No issues found by pyflakes."

def run_complexity(filepath: str) -> str:
    """Run radon cyclomatic complexity analysis."""
    result = subprocess.run(
        [sys.executable, "-m", "radon", "cc", filepath, "-s"],
        capture_output=True, text=True
    )
    return result.stdout.strip() or "No complexity data."

def run_tests(test_dir: str, timeout: int = 30) -> str:
    """Run pytest on a directory and return the summary."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", test_dir, "-v", "--tb=short", "--no-header"],
        capture_output=True, text=True, timeout=timeout
    )
    # Return last 3000 chars — test output can be very long
    output = (result.stdout + result.stderr)[-3000:]
    return output or "No test output."

def execute_code(code: str) -> str:
    """Execute Python code and return formatted result."""
    result = execute_python(code)
    return result.to_tool_string()
```

### Tool schemas for Code Review Agent

```python
# tools/schemas.py

CODE_REVIEW_TOOLS = [
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
```

---

## Day 3–4 — Code Review Agent (7 hrs)

**Goal:** an agent that reads Python code, lints it, runs complexity checks, reproduces each bug it finds with a test snippet, and writes a structured markdown review.

### System Prompt

```python
# agents/prompts.py

CODE_REVIEW_SYSTEM = """
You are a senior Python engineer conducting a thorough code review.

YOUR REVIEW PROCESS — follow this order exactly:

1. LIST THE DIRECTORY to understand project structure.
2. READ EVERY Python file relevant to the review.
3. RUN THE LINTER (pyflakes) on each file. Record all issues.
4. RUN COMPLEXITY CHECK (radon). Flag any function with score > 7.
5. MANUAL REVIEW — read the code carefully and identify:
   - Logic bugs (off-by-one, wrong conditionals, missed edge cases)
   - Security issues (SQL injection, path traversal, hardcoded credentials)
   - Performance issues (O(n²) where O(n) is possible, unnecessary copies)
   - Bad practices (bare except, mutable default arguments, global state)
6. VERIFY each bug you found: write a short code snippet that REPRODUCES the bug
   and execute it. Only include bugs you can demonstrate.
7. WRITE the final review report to outputs/reviews/.

REPORT FORMAT:
## Code Review: [filename]

### Summary
One paragraph overview of overall code quality.

### Issues Found

#### [CRITICAL/HIGH/MEDIUM/LOW] Issue Name
**Location:** function_name(), line ~N
**Description:** What the problem is.
**Reproduction:**
```python
# code that demonstrates the bug
```
**Expected:** what should happen
**Actual:** what happens instead
**Fix:**
```python
# corrected code
```

### Metrics
- Files reviewed: N
- Linter issues: N
- Complexity violations: N
- Bugs verified: N / N found

IMPORTANT:
- Never claim a bug exists without executing code that proves it.
- If you cannot reproduce it, list it as "Unverified / Suspected" with lower confidence.
- Include the actual execution output in your notes.
"""
```

### The Agent

```python
# agents/code_review.py
import os, json
from openai import OpenAI
from dotenv import load_dotenv
from tools.schemas import CODE_REVIEW_TOOLS
from tools.file_tools import read_file, list_directory, write_file
from tools.execution_tools import run_linter, run_complexity, execute_code
from agents.prompts import CODE_REVIEW_SYSTEM

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

MODEL = "openrouter/owl-alpha"

TOOL_DISPATCH = {
    "read_file": lambda args: read_file(args["filepath"]),
    "list_directory": lambda args: list_directory(args["dirpath"]),
    "run_linter": lambda args: run_linter(args["filepath"]),
    "run_complexity": lambda args: run_complexity(args["filepath"]),
    "execute_code": lambda args: execute_code(args["code"]),
    "write_file": lambda args: write_file(args["filepath"], args["content"]),
}

def run_code_review(target: str, max_iterations: int = 25) -> str:
    """
    target: a file path or directory path to review
    """
    messages = [
        {"role": "system", "content": CODE_REVIEW_SYSTEM},
        {
            "role": "user",
            "content": (
                f"Please conduct a thorough code review of: {target}\n\n"
                "Follow your review process exactly. Verify every bug you find "
                "by executing a reproduction snippet. Write the final report to "
                f"outputs/reviews/review_{os.path.basename(target)}.md"
            )
        }
    ]
    
    tool_call_count = 0
    
    for i in range(max_iterations):
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=4096,
            tools=CODE_REVIEW_TOOLS,
            messages=messages
        )
        
        msg = response.choices[0].message
        finish_reason = response.choices[0].finish_reason
        
        if msg.content:
            print(f"\n💭 {msg.content[:300]}{'...' if len(msg.content) > 300 else ''}")
        
        if finish_reason == "stop":
            print(f"\n✅ Review complete. {tool_call_count} tool calls made.")
            return msg.content or "Done."
        
        if finish_reason == "tool_calls":
            messages.append({
                "role": "assistant",
                "content": msg.content,
                "tool_calls": msg.tool_calls
            })
            
            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments)
                tool_name = tc.function.name
                
                print(f"\n🔧 {tool_name}({', '.join(f'{k}={repr(v)[:50]}' for k, v in args.items())})")
                
                if tool_name in TOOL_DISPATCH:
                    result = TOOL_DISPATCH[tool_name](args)
                else:
                    result = f"Unknown tool: {tool_name}"
                
                tool_call_count += 1
                print(f"   → {result[:150]}{'...' if len(result) > 150 else ''}")
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": str(result)
                })
    
    return "Max iterations reached"


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "test_targets/"
    run_code_review(target)
```

### Buggy target files to test against

Create these intentionally broken files — the agent should catch all of these:

```python
# test_targets/buggy_api.py
import json

# BUG 1: mutable default argument — classic Python trap
def add_item(item, cart=[]):
    cart.append(item)
    return cart

# BUG 2: bare except swallows all errors including KeyboardInterrupt
def load_config(path):
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return {}

# BUG 3: off-by-one in range — misses the last element
def get_pairs(items):
    pairs = []
    for i in range(len(items) - 1):
        pairs.append((items[i], items[i+1]))
    return pairs

# BUG 4: O(n²) — list membership check inside loop, should use a set
def find_duplicates(items):
    seen = []
    duplicates = []
    for item in items:
        if item in seen:        # O(n) lookup per item = O(n²) total
            duplicates.append(item)
        seen.append(item)
    return duplicates

# BUG 5: SQL injection — string interpolation into query
def get_user(db_cursor, username):
    query = f"SELECT * FROM users WHERE username = '{username}'"
    db_cursor.execute(query)
    return db_cursor.fetchone()
```

```python
# test_targets/insecure_auth.py

# BUG 1: hardcoded credentials
SECRET_KEY = "super_secret_123"
DB_PASSWORD = "admin1234"

# BUG 2: timing attack vulnerability — string comparison not constant time
def verify_token(provided: str, expected: str) -> bool:
    return provided == expected   # should use hmac.compare_digest

# BUG 3: path traversal — user input goes directly into file path
def read_user_file(username: str) -> str:
    path = f"/app/user_data/{username}/profile.txt"
    with open(path) as f:        # username could be "../../etc/passwd"
        return f.read()

# BUG 4: password stored in plaintext
users_db = {
    "alice": "password123",
    "bob": "qwerty"
}

def login(username: str, password: str) -> bool:
    return users_db.get(username) == password
```

**What to look for when evaluating the agent's output:**
- Did it run the linter before any manual analysis?
- Did it execute a snippet that *actually demonstrates* each bug?
- Did the mutable default argument bug get caught (this is the hardest one)?
- Did it catch the SQL injection AND the path traversal (two different categories)?
- Does the report include actual execution output, not just the code?

---

## Day 5 — Data Analyst Agent: Tools + Prompt (3 hrs)

**Goal:** build the tool set for a stateful, multi-turn data analysis session.

The key design challenge here is **telling the model what state already exists.** After the user loads a CSV, the agent should know on the next turn that `df` is already in scope — without re-reading the file.

### Analysis Tools

```python
# tools/analysis_tools.py
import pandas as pd
from pathlib import Path
from tabulate import tabulate

def describe_csv(filepath: str) -> str:
    """Give the model a summary of the CSV before it writes any code."""
    try:
        df = pd.read_csv(filepath)
        lines = [
            f"File: {filepath}",
            f"Shape: {df.shape[0]} rows × {df.shape[1]} columns",
            f"\nColumns:",
        ]
        for col in df.columns:
            dtype = str(df[col].dtype)
            nulls = df[col].isnull().sum()
            if df[col].dtype in ("int64", "float64"):
                lines.append(
                    f"  {col} ({dtype}): min={df[col].min()}, "
                    f"max={df[col].max()}, nulls={nulls}"
                )
            else:
                n_unique = df[col].nunique()
                sample = df[col].dropna().head(3).tolist()
                lines.append(
                    f"  {col} ({dtype}): {n_unique} unique values, "
                    f"sample={sample}, nulls={nulls}"
                )
        lines.append(f"\nFirst 3 rows:\n{tabulate(df.head(3), headers='keys', tablefmt='simple')}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error reading CSV: {e}"
```

### Tool Schemas for Data Analyst

```python
# Add to tools/schemas.py

DATA_ANALYST_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "describe_csv",
            "description": (
                "Get a structural summary of a CSV file: column names, data types, "
                "value ranges, null counts, and a sample of rows. "
                "ALWAYS call this before writing any analysis code for a new file."
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
            "name": "execute_analysis",
            "description": (
                "Execute Python code in a persistent session. "
                "pd (pandas), plt (matplotlib.pyplot), and sns (seaborn) are already imported. "
                "Variables defined in previous calls are still in scope — "
                "you do NOT need to reload the CSV if df is already defined. "
                "To save a chart: plt.savefig('outputs/charts/name.png'); plt.close(). "
                "Always print() your final results so they appear in the output."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code to execute in the persistent session."
                    }
                },
                "required": ["code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_session_state",
            "description": (
                "List all variables currently defined in the analysis session. "
                "Call this if you're unsure whether df or other variables already exist."
            ),
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "reset_session",
            "description": (
                "Clear all variables from the session and start fresh. "
                "Use this when switching to a completely different dataset or analysis."
            ),
            "parameters": {"type": "object", "properties": {}}
        }
    }
]
```

---

## Day 6 — Data Analyst Agent: Full Implementation (4 hrs)

### The Agent

```python
# agents/data_analyst.py
import os, json
from openai import OpenAI
from dotenv import load_dotenv
from sandbox.namespace import PersistentNamespace
from tools.schemas import DATA_ANALYST_TOOLS
from tools.analysis_tools import describe_csv

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

MODEL = "openrouter/owl-alpha"

DATA_ANALYST_SYSTEM = """
You are a data analyst assistant. You answer questions about datasets by writing
and executing Python code.

WORKFLOW:
1. When given a new file, call describe_csv first to understand its structure.
2. Write pandas/matplotlib code and call execute_analysis.
3. If the code fails, READ the error carefully, fix the code, and retry.
   Most errors are: wrong column name (check the describe output), wrong dtype,
   or a null value you didn't handle. Fix one thing at a time.
4. Always print() your final answer. A chart alone is not enough — summarize
   what the chart shows in text too.

RULES:
- pd, plt, sns are already imported. Do not re-import them.
- Check get_session_state if unsure what variables exist.
- After saving a chart, always call plt.close() to avoid figure bleed.
- When asked for a trend, include both the chart and a written interpretation.
- Never guess at column names. Always verify from describe_csv output first.
"""

class DataAnalystAgent:
    def __init__(self):
        self.session = PersistentNamespace()
        self.conversation: list[dict] = [
            {"role": "system", "content": DATA_ANALYST_SYSTEM}
        ]
    
    def _dispatch(self, tool_name: str, args: dict) -> str:
        if tool_name == "describe_csv":
            return describe_csv(args["filepath"])
        
        elif tool_name == "execute_analysis":
            result = self.session.execute(args["code"])
            response = result.to_tool_string()
            # Append session state so agent always knows what's in scope
            if result.success and result.local_vars:
                response += f"\n\nSession variables now in scope: {list(result.local_vars.keys())}"
            return response
        
        elif tool_name == "get_session_state":
            vars_in_scope = self.session.get_defined_vars()
            if not vars_in_scope:
                return "Session is empty — no variables defined yet."
            return f"Variables currently in scope: {vars_in_scope}"
        
        elif tool_name == "reset_session":
            self.session.reset()
            return "Session cleared. All variables removed."
        
        return f"Unknown tool: {tool_name}"
    
    def chat(self, user_message: str) -> str:
        """Send one user message and run the agent loop until it responds."""
        self.conversation.append({"role": "user", "content": user_message})
        
        for _ in range(20):  # max tool calls per user message
            response = client.chat.completions.create(
                model=MODEL,
                max_tokens=2048,
                tools=DATA_ANALYST_TOOLS,
                messages=self.conversation
            )
            
            msg = response.choices[0].message
            finish_reason = response.choices[0].finish_reason
            
            if msg.content:
                print(f"\n💭 {msg.content[:200]}{'...' if len(msg.content) > 200 else ''}")
            
            if finish_reason == "stop":
                self.conversation.append({
                    "role": "assistant",
                    "content": msg.content
                })
                return msg.content or ""
            
            if finish_reason == "tool_calls":
                self.conversation.append({
                    "role": "assistant",
                    "content": msg.content,
                    "tool_calls": msg.tool_calls
                })
                
                for tc in msg.tool_calls:
                    args = json.loads(tc.function.arguments)
                    print(f"\n🔧 {tc.function.name}({str(args)[:80]})")
                    
                    result = self._dispatch(tc.function.name, args)
                    print(f"   → {result[:200]}{'...' if len(result) > 200 else ''}")
                    
                    self.conversation.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result
                    })
        
        return "Max iterations reached for this message."


def run_interactive_session():
    """Multi-turn REPL for data analysis."""
    agent = DataAnalystAgent()
    print("Data Analyst Agent — type 'quit' to exit, 'reset' to clear session\n")
    
    while True:
        user_input = input("\nYou: ").strip()
        if not user_input:
            continue
        if user_input.lower() == "quit":
            break
        if user_input.lower() == "reset":
            agent = DataAnalystAgent()
            print("Session reset.")
            continue
        
        answer = agent.chat(user_input)
        print(f"\nAgent: {answer}")


if __name__ == "__main__":
    run_interactive_session()
```

### Sample CSV files to test with

Create these datasets so you have realistic data to analyze:

```python
# create_test_data.py — run once to generate test CSVs
import pandas as pd
import numpy as np

np.random.seed(42)
n = 200

# Sales dataset
sales = pd.DataFrame({
    "date": pd.date_range("2024-01-01", periods=n, freq="D"),
    "product": np.random.choice(["Laptop", "Phone", "Tablet", "Watch"], n),
    "region": np.random.choice(["North", "South", "East", "West"], n),
    "units_sold": np.random.randint(1, 50, n),
    "unit_price": np.random.choice([999, 599, 399, 249], n),
    "discount_pct": np.random.choice([0, 5, 10, 15, 20], n),
})
sales["revenue"] = sales["units_sold"] * sales["unit_price"] * (1 - sales["discount_pct"]/100)
# Introduce some nulls for realism
sales.loc[np.random.choice(n, 10), "discount_pct"] = np.nan
sales.to_csv("datasets/sales.csv", index=False)

# Students dataset
students = pd.DataFrame({
    "student_id": range(1, 101),
    "name": [f"Student_{i}" for i in range(1, 101)],
    "major": np.random.choice(["CS", "Math", "Physics", "Engineering"], 100),
    "year": np.random.choice([1, 2, 3, 4], 100),
    "gpa": np.round(np.random.uniform(2.0, 4.0, 100), 2),
    "assignments_submitted": np.random.randint(5, 20, 100),
    "passed": np.random.choice([True, False], 100, p=[0.8, 0.2]),
})
students.to_csv("datasets/students.csv", index=False)

print("Created datasets/sales.csv and datasets/students.csv")
```

### Multi-turn test conversation

Run these questions sequentially in one session to test the stateful behavior:

```
Session turn 1: "Load datasets/sales.csv and give me a summary of the data."
Session turn 2: "What are the top 3 products by total revenue?"
Session turn 3: "Plot monthly revenue trend as a line chart and save it."
Session turn 4: "Which region has the highest average discount?"
Session turn 5: "Is there a correlation between discount percentage and units sold?"
Session turn 6: "Now load datasets/students.csv — reset the session first."
Session turn 7: "What's the GPA distribution by major? Show as a box plot."
```

**The critical test:** after turn 2, the agent should NOT reload the CSV on turn 3. It already has `df` in scope. If it calls `describe_csv` again unnecessarily, your system prompt needs tightening.

---

## Day 7 — Error-Repair Loop Deep Dive + Reflection (2 hrs)

The error-repair loop is the single most important pattern in this week — it's how code-execution agents become useful in practice rather than one-shot. Spend Day 7 stress-testing it.

### Intentional failure injection

For the Data Analyst Agent, test what happens when you ask about columns that don't exist:

```
"What is the average sale_amount per region?"  ← 'sale_amount' doesn't exist, it's 'revenue'
"Show me the semester grade distribution"       ← this column doesn't exist at all
"Calculate profit margin for each product"     ← requires a 'cost' column that's absent
```

For each of these, the agent should: (1) write code, (2) get a KeyError or similar, (3) read the traceback, (4) check the column names, (5) either use the correct column or tell you the data doesn't have what you asked for. If it hallucinate-fixes by inventing column names, that's a system prompt problem.

### Questions to answer in REFLECTIONS.md

1. **Strategy A vs B tradeoffs.** You used subprocess for Code Review and exec() for Data Analyst. Could you have used subprocess for the Data Analyst? What would the implementation look like? What would you lose?

2. **The repair loop structure.** When the Data Analyst agent gets a KeyError, what does the conversation history look like at that moment? Draw it out — show the user message, the tool call, the error tool result, and the next assistant message. How does the model "know" to try a different column name?

3. **Context window pressure.** Run a 10-turn data analysis session and print `len(json.dumps(conversation))` after each turn. At what point does the conversation history start getting large? What would you do to manage this in a production system?

4. **The verification principle.** The Code Review Agent's system prompt says "never claim a bug exists without executing code that proves it." Why does this matter? What happens if you remove that constraint — what does the agent produce? Try it.

5. **Security gap audit.** Look at your blocked imports list in `executor.py`. List three ways a malicious code snippet could still cause harm despite your blocklist. This is not hypothetical — these are real vectors you'd close in production.

---

## Resources Reference Card

### All free
| Resource | URL |
|---|---|
| Python subprocess docs | https://docs.python.org/3/library/subprocess.html |
| pyflakes | https://github.com/PyCQA/pyflakes |
| radon (complexity) | https://radon.readthedocs.io |
| pandas docs | https://pandas.pydata.org/docs |
| E2B (production sandboxes, free tier) | https://e2b.dev — look at this for Week 4+ when you need real isolation |
| Anthropic: Tool Use patterns | https://github.com/anthropics/anthropic-cookbook/tree/main/patterns/agents |

### Production sandboxing note (Week 4+ context)
For learning this week, subprocess + a blocklist is fine. In production agents (like your Week 4 Recruitment Agent running untrusted CV-parsing code), you'd use a proper sandboxed environment. Two free-tier options worth knowing: **E2B** (managed sandboxes, 100 hrs/month free) and **Modal** (serverless containers, $30/month free credits). You don't need them now, but they exist.

---

## End-of-Week Checklist

Before moving to Week 3, answer yes to all of these:

- [ ] My subprocess executor enforces a timeout — I've verified it doesn't hang on `while True: pass`
- [ ] My executor blocks dangerous imports statically before spawning a process
- [ ] The Code Review Agent verifies every bug by executing a reproduction snippet
- [ ] The Code Review Agent caught at least 4 of 5 bugs in `buggy_api.py`
- [ ] The Code Review Agent caught the SQL injection and timing attack in `insecure_auth.py`
- [ ] The Data Analyst Agent does NOT reload the CSV on turn 2 if it already loaded it on turn 1
- [ ] The Data Analyst Agent recovers from a KeyError (wrong column name) without crashing
- [ ] I can explain the difference between Strategy A and Strategy B and when each is appropriate
- [ ] I've answered all five REFLECTIONS.md questions in writing
- [ ] I can draw the conversation history of a 3-step error-repair loop from memory

## What Week 3 Builds On This

Week 3 adds memory and RAG — the agent will retrieve context from past sessions and documents rather than starting fresh each time. The persistent namespace you built in Week 2 is conceptually the same problem as session memory; RAG is just solving it at a larger scale with vector search instead of a Python dict.
