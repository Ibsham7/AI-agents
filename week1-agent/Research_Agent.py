import os, json
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from datetime import datetime
from pathlib import Path
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Search the web for current, factual information. Use this when the "
                "question requires up-to-date data, recent events, specific facts you "
                "don't know, or verification of claims. Returns a list of relevant "
                "results with titles, URLs, and content snippets."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A specific, targeted search query. Be precise."
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Number of results to return. Default 5, max 10.",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": (
                "Evaluate a mathematical expression. Use ONLY for arithmetic, "
                "percentages, and numeric calculations. Do NOT use for text processing."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string"}
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "count_words",
            "description": (
                "Count words, characters, or sentences in a piece of text. "
                "Use when the task requires measuring text length or content volume."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to analyze"},
                    "count_type": {
                        "type": "string",
                        "enum": ["words", "characters", "sentences"],
                        "description": "What to count"
                    }
                },
                "required": ["text", "count_type"]
            }
        }
    }
]


class ToolResult:
    def __init__(self, content: str, is_error: bool = False):
        self.content = content
        self.is_error = is_error
    
    def to_api_format(self, tool_call_id: str) -> dict:
        # In OpenAI format, errors are just returned as string content —
        # the model reads the error text and decides what to do next.
        # Prefix error messages clearly so the model recognises them.
        content = f"ERROR: {self.content}" if self.is_error else self.content
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": content
        }

def execute_tool_safe(name: str, input_data: dict) -> ToolResult: #type: ignore
    try:
        if name == "web_search":
            results = tavily.search(
                query=input_data["query"],
                max_results=input_data.get("max_results", 5)
            )
            if not results.get("results"):
                # Not an error — just no results. Model should try a different query.
                return ToolResult(
                    "No results found for this query. Try a different search term or broader query."
                )
            
            formatted = []
            for r in results.get("results", []):
                formatted.append(f"**{r['title']}**\nURL: {r['url']}\n{r['content']}\n")
            return ToolResult("\n---\n".join(formatted))
            
        elif name == "calculator":
            # Catch eval errors specifically
            try:
                result = eval(input_data["expression"], {"__builtins__": {}})
                return ToolResult(str(result))
            except ZeroDivisionError:
                return ToolResult("Error: Division by zero", is_error=True)
            except SyntaxError as e:
                return ToolResult(f"Error: Invalid expression syntax — {e}", is_error=True)
            except Exception as e:
                return ToolResult(f"Error: {e}", is_error=True)
    
    except Exception as e:
        # Network errors, API timeouts, etc.
        return ToolResult(
            f"Tool '{name}' failed with error: {str(e)}. "
            "Consider trying a different approach.",
            is_error=True
        )
    

RESEARCH_AGENT_SYSTEM = """
You are a rigorous research agent. When given a research question, you:

1. PLAN: Before taking any action, briefly state your research plan — what you need to find out and in what order.

2. SEARCH ITERATIVELY: Run multiple targeted searches. Start broad, then narrow based on what you find. Never rely on a single search result.

3. REASON ALOUD: After each tool result, explicitly state what you learned and what gap remains. This keeps your research on track.

4. SYNTHESIZE: When you have enough information, produce a structured report.

REPORT FORMAT:
## [Topic Title]

### Summary
2-3 sentence executive summary.

### Key Findings
- Finding 1 (source: URL)
- Finding 2 (source: URL)
- ...

### Analysis
Your synthesis and interpretation of the findings.

### Sources
1. [Title](URL)
2. ...

RULES:
- Minimum 3 searches before concluding (more for complex topics)
- Every factual claim must be traceable to a search result
- If search results conflict, note the conflict and explain your judgment
- Do not make up facts. If you can't find something, say so.
"""

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

MODEL = "openrouter/owl-alpha"

def run_research_agent(query : str , max_iterations: int = 15) -> dict: # type: ignore
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
    
    print(f"\n Research Query: {query}\n{'='*60}")
    
    for i in range(max_iterations):
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=2048,
            tools=TOOL_DEFINITIONS,  # type: ignore[arg-type]
            messages=messages   # type: ignore
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
            messages.append({
                "role": "assistant",
                "content": msg.content,
                "tool_calls": msg.tool_calls
            }) # type: ignore
            
            for tool_call in msg.tool_calls:  # type: ignore
                tool_input = json.loads(tool_call.function.arguments) # type: ignore
                print(f"\n🔧 Tool: {tool_call.function.name}") # type: ignore
                print(f"   Input: {json.dumps(tool_input, indent=2)}")

                tool_result = execute_tool_safe(tool_call.function.name, tool_input) #type: ignore
                result = tool_result.content
                print(f"   Result preview: {result[:200]}...")
                
                tool_log.append({
                    "iteration": i + 1,
                    "tool": tool_call.function.name, #type: ignore
                    "input": tool_input,
                    "result_length": len(result)
                })
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
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