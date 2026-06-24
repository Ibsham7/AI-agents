import sys
import os
import json
from dotenv import load_dotenv
from openai import OpenAI

# Load .env
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
load_dotenv(env_path)

# Add week1-agent directory to Python path so we can import 02_multi_tool
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import importlib.util
spec = importlib.util.spec_from_file_location("multi_tool", os.path.join(parent_dir, "02_multi_tool.py"))
multi_tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(multi_tool)

# Setup OpenAI client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

MODEL = "openai/gpt-oss-120b:free"

def run_agent(user_query: str, log_list: list, max_iterations: int = 10) -> str:
    messages = [{"role": "user", "content": user_query}]
    
    for iteration in range(max_iterations):
        log_list.append(f"\n--- Iteration {iteration + 1} ---")
        
        # Call the model with our multi-tool definitions
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=1024,
            tools=multi_tool.TOOL_DEFINITIONS,
            messages=messages
        )
        
        msg = response.choices[0].message
        finish_reason = response.choices[0].finish_reason
        log_list.append(f"Finish reason: {finish_reason}")
        
        # Case 1: Model is done
        if finish_reason == "stop":
            return msg.content or "No response"
        
        # Case 2: Model wants to use a tool
        if finish_reason == "tool_calls":
            messages.append({
                "role": "assistant",
                "content": msg.content,
                "tool_calls": msg.tool_calls
            })
            
            # Process every tool call
            for tc in msg.tool_calls:
                tool_input = json.loads(tc.function.arguments)
                log_list.append(f"Tool called: {tc.function.name}")
                log_list.append(f"Input: {tool_input}")
                
                # Execute the tool using 02_multi_tool
                result = multi_tool.execute_tool(tc.function.name, tool_input)
                log_list.append(f"Result: {result}")
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result
                })
    
    return "Max iterations reached"

def run_tests():
    output_dir = os.path.join(parent_dir, "outputs")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "test_multi_tool_results.txt")
    
    # Complex queries that will require different tools
    queries = [
        "What is 15 multiplied by 20?",
        "Search the web for the latest news about SpaceX and summarize it in 2 sentences.",
        "Can you count the number of words in this exact sentence?"
    ]
    
    logs = []
    
    for q in queries:
        print(f"Running agent for query: {q}")
        logs.append(f"\n{'='*60}\nQuery: {q}\n{'='*60}")
        answer = run_agent(q, logs)
        logs.append(f"\nFinal Answer: {answer}")
        
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(logs))
        
    print(f"\nTests completed! Full agent trace saved to: {output_file}")

if __name__ == "__main__":
    run_tests()
