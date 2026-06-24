# agent/tools.py — Tool definitions and executors
import os, json
from tavily import TavilyClient

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# OpenAI-compatible tool schema format (works with OpenRouter)
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

    