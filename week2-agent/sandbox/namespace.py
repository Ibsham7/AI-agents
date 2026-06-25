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