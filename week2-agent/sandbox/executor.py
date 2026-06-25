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