# 03_react_loop.py
import os, json
from openai import OpenAI
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from agent.tools import TOOL_DEFINITIONS, execute_tool , execute_tool_safe
from agent.prompts import RESEARCH_AGENT_SYSTEM

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

MODEL = "openrouter/owl-alpha"

def run_research_agent(query: str, max_iterations: int = 15) -> dict:
    """
    Returns a dict with: answer, tool_call_log, token_usage, duration
    """
    messages = [
        {"role": "system", "content": RESEARCH_AGENT_SYSTEM},
        {"role": "user", "content": query}
    ]
    tool_log = []
    total_tokens = {"input": 0, "output": 0}
    start = datetime.now()
    
    print(f"\n🔍 Research Query: {query}\n{'='*60}")
    
    for i in range(max_iterations):
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=2048,
            tools=TOOL_DEFINITIONS,
            messages=messages
        )
        
        msg = response.choices[0].message
        finish_reason = response.choices[0].finish_reason
        
        # Track tokens
        if response.usage:
            total_tokens["input"] += response.usage.prompt_tokens
            total_tokens["output"] += response.usage.completion_tokens
        
        # Print the model's reasoning (text content)
        if msg.content:
            print(f"\n💭 Thought:\n{msg.content}")
        
        if finish_reason == "stop":
            duration = (datetime.now() - start).seconds
            return {
                "answer": msg.content or "No response",
                "tool_calls": len(tool_log),
                "tool_log": tool_log,
                "tokens": total_tokens,
                "duration_sec": duration
            }
        
        if finish_reason == "tool_calls":
            # Append assistant message (with tool_calls) to history
            messages.append({
                "role": "assistant",
                "content": msg.content,
                "tool_calls": msg.tool_calls
            })
            
            for tc in msg.tool_calls:
                tool_input = json.loads(tc.function.arguments)
                print(f"\n🔧 Tool: {tc.function.name}")
                print(f"   Input: {json.dumps(tool_input, indent=2)}")
                
                tool_result = execute_tool_safe(tc.function.name, tool_input)
                result = tool_result.content
                print(f"   Result preview: {result[:200]}...")
                
                tool_log.append({
                    "iteration": i + 1,
                    "tool": tc.function.name,
                    "input": tool_input,
                    "result_length": len(result)
                })
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result
                })
    
    return {"answer": "Max iterations reached", "tool_log": tool_log}

def save_report(query: str, result: dict):
    Path("outputs/react_loop").mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"outputs/react_loop/report_{timestamp}.md"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# Research Report\n\n")
        f.write(f"**Query:** {query}\n\n")
        f.write(f"**Stats:** {result['tool_calls']} tool calls | ")
        f.write(f"{result['tokens']['input']+result['tokens']['output']} total tokens | ")
        f.write(f"{result['duration_sec']}s\n\n")
        f.write("---\n\n")
        f.write(result["answer"])
    
    print(f"\n📄 Report saved: {filename}")
    return filename

if __name__ == "__main__":
    query = input("Research query: ")
    result = run_research_agent(query)
    save_report(query, result)
    print(f"\n✅ Done. Used {result['tool_calls']} tools, "
          f"{result['tokens']['input']+result['tokens']['output']} tokens.")