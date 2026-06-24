
# 00_raw_api_call.py — Run this first, read the output carefully
import os, json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

MODEL = "openrouter/owl-alpha"

# Step 1: No tools — just a plain call
response = client.chat.completions.create(
    model=MODEL,
    max_tokens=512,
    messages=[{"role": "user", "content": "What is 847 * 23?"}]
)
print("=== PLAIN RESPONSE ===")
print(json.dumps(response.model_dump(), indent=2))
# Study: choices[0].finish_reason, choices[0].message.content, usage

# Step 2: With a tool defined — model should choose to use it
response = client.chat.completions.create(
    model=MODEL,
    max_tokens=512,
    tools=[{
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Perform arithmetic calculations. Use this for any math.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "A math expression to evaluate, e.g. '847 * 23'"
                    }
                },
                "required": ["expression"]
            }
        }
    }],
    messages=[{"role": "user", "content": "What is 847 * 23?"}]
)
print("\n=== TOOL USE RESPONSE ===")
print(json.dumps(response.model_dump(), indent=2))
# Study: finish_reason is now "tool_calls"
# choices[0].message.tool_calls[0] has: id, function.name, function.arguments (JSON string)
# This is the model saying "please run this function for me"

# Step 3: Actually running the tool and getting the final answer!
from agent.tools import calculator

message = response.choices[0].message
if message.tool_calls:
    tool_call = message.tool_calls[0]
    
    # 1. Check which tool the model wants to run
    if tool_call.function.name == "calculator":
        # 2. Extract the arguments (it returns a JSON string, so we parse it)
        args = json.loads(tool_call.function.arguments)
        expression = args.get("expression")
        
        print(f"\n[Executing Tool] Model requested calculator for: {expression}")
        
        # 3. Run our python function!
        result = calculator(expression)
        print(f"[Tool Result] The answer is: {result}")
        
        # 4. Send the result back to the model
        messages = [
            {"role": "user", "content": "What is 847 * 23?"},
            message, # We must include the model's tool call message
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_call.function.name,
                "content": result # The result of our python function
            }
        ]
        
        # 5. Make the final API call
        final_response = client.chat.completions.create(
            model=MODEL,
            max_tokens=512,
            tools=[{
                "type": "function",
                "function": {
                    "name": "calculator",
                    "description": "Perform arithmetic calculations. Use this for any math.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "A math expression to evaluate, e.g. '847 * 23'"
                            }
                        },
                        "required": ["expression"]
                    }
                }
            }],
            messages=messages
        )
        
        print("\n=== FINAL RESPONSE AFTER TOOL USE ===")
        print(final_response.choices[0].message.content)