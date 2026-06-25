import os, json
from typing import Any
from openai import OpenAI
from dotenv import load_dotenv
from tools.Schemas import CODE_REVIEW_TOOLS
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
    messages: list[Any] = [
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
    directory_cache: dict[str, str] = {}
    
    for i in range(max_iterations):
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=4096,
            tools=CODE_REVIEW_TOOLS, 
            messages=messages
        )
        
        msg : Any = response.choices[0].message
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
                cache_key = None

                if tool_name == "list_directory":
                    cache_key = args["dirpath"]
                
                print(f"\n🔧 {tool_name}({', '.join(f'{k}={repr(v)[:50]}' for k, v in args.items())})")
                
                if cache_key is not None and cache_key in directory_cache:
                    result = directory_cache[cache_key]
                elif tool_name in TOOL_DISPATCH:
                    result = TOOL_DISPATCH[tool_name](args)
                    if cache_key is not None:
                        directory_cache[cache_key] = result
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