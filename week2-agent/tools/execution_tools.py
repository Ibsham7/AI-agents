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