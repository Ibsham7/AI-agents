# 01_single_tool.py
import os, json
from agent.tools import calculator
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

MODEL = "openrouter/owl-alpha"

# ─── Tool Definition ──────────────────────────────────────────────────────────
TOOLS = [{
    "type": "function",
    "function": {
        "name": "calculator",
        "description": (
            "Evaluate a mathematical expression. Use for any arithmetic, "
            "percentages, unit conversions, or multi-step calculations. "
            "Pass a valid Python math expression as a string."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Python-evaluable math expression, e.g. '(100 * 1.15) ** 2'"
                }
            },
            "required": ["expression"]
        }
    }
}]

# ─── Tool Executor ────────────────────────────────────────────────────────────
def execute_tool(tool_name: str, tool_input: dict) -> str:
    if tool_name == "calculator":
        try:
            # eval() is fine for learning; in production, use a safe parser
            result = calculator(tool_input["expression"])
            return str(result)
        except Exception as e:
            return f"Error: {e}"
    return f"Unknown tool: {tool_name}"

# ─── Agent Loop ───────────────────────────────────────────────────────────────
def run_agent(user_query: str, max_iterations: int = 10) -> str:
    messages = [{"role": "user", "content": user_query}]
    
    for iteration in range(max_iterations):
        print(f"\n--- Iteration {iteration + 1} ---")
        
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=1024,
            tools=TOOLS,
            messages=messages
        )
        
        msg = response.choices[0].message
        finish_reason = response.choices[0].finish_reason
        print(f"Finish reason: {finish_reason}")
        
        # Case 1: Model is done
        if finish_reason == "stop":
            return msg.content or "No response"
        
        # Case 2: Model wants to use a tool
        if finish_reason == "tool_calls":
            # Append the assistant message (with tool_calls) to history
            messages.append({
                "role": "assistant",
                "content": msg.content,
                "tool_calls": msg.tool_calls
            })
            
            # Process every tool call in this response (there can be multiple)
            for tc in msg.tool_calls:
                tool_input = json.loads(tc.function.arguments)
                print(f"Tool called: {tc.function.name}")
                print(f"Input: {tool_input}")
                
                result = execute_tool(tc.function.name, tool_input)
                print(f"Result: {result}")
                
                # Each result goes back as its own "tool" role message
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,   # Must match exactly
                    "content": result
                })
    
    return "Max iterations reached"

# ─── Test It ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    queries = [
        "If I invest $5000 at 7% annual return compounded monthly for 10 years, how much will I have?",
        "A store is selling 3 items: a shirt for $45.99, pants for $89.50, and shoes for $120. What's the total after 15% discount and 8% tax?",
    ]
    for q in queries:
        print(f"\n{'='*60}\nQuery: {q}\n{'='*60}")
        answer = run_agent(q)
        print(f"\nFinal Answer: {answer}")