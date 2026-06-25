from tavily import TavilyClient
from dotenv import load_dotenv

import os, json
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

def calculator(expression: str) -> str:
    """
    A simple calculator that evaluates a mathematical expression.
    For a beginner, we use eval(), but in production, you should use a safer parser!
    """
    try:
        # Evaluate the mathematical expression
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error evaluating expression: {e}"

def execute_tool(name: str, input_data: dict) -> str:
    if name == "web_search":
        results = tavily.search(
            query=input_data["query"],
            max_results=input_data.get("max_results", 5)
        )
        # Format results for the model to read
        formatted = []
        for r in results.get("results", []):
            formatted.append(f"**{r['title']}**\nURL: {r['url']}\n{r['content']}\n")
        return "\n---\n".join(formatted) or "No results found."
    
    elif name == "calculator":
        try:
            return str(eval(input_data["expression"]))
        except Exception as e:
            return f"Calculation error: {e}"
    
    elif name == "count_words":
        text = input_data["text"]
        count_type = input_data["count_type"]
        if count_type == "words":
            return str(len(text.split()))
        elif count_type == "characters":
            return str(len(text))
        elif count_type == "sentences":
            import re
            return str(len(re.split(r'[.!?]+', text.strip())))
    
    return f"Unknown tool: {name}"
    
# 04_error_recovery.py — Add this to your execute_tool function

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

def execute_tool_safe(name: str, input_data: dict) -> ToolResult:
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