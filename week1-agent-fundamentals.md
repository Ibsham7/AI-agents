# Week 1 — Tool-Calling Agents From Scratch
### Detailed Daily Workflow | Intensive Track (20+ hrs/week)

---

## What You Will Have Built by End of Week 1

A fully hand-rolled, multi-tool Research Report Agent in raw Python — no LangChain, no LangGraph, no abstraction. It will:
- Accept a research question
- Decide which tools to use and in what order
- Execute web searches, scrape page content, and run a calculator
- Loop autonomously until it judges the answer complete
- Write a cited, structured markdown report to disk

Every component — the loop, the tool dispatcher, error recovery, multi-turn history — written by you. This is the highest-leverage week on the entire roadmap.

---

## Before Day 1 — Setup Checklist (2–3 hrs)

### API Keys (all free tiers, no credit card required)

| Service | What it's for | Free tier | Signup link |
|---|---|---|---|
| OpenRouter | LLM API gateway — access free models via one key | 50 req/day, 20 req/min, no card needed | https://openrouter.ai |
| Tavily | Web search for agents | 1,000 searches/month free | https://app.tavily.com |
| Serper | Google SERP fallback | 2,500 queries/month free | https://serper.dev |

> **On the Anthropic API:** Anthropic stopped giving free signup credits to free-tier accounts. Don't worry — OpenRouter gives you free access to models that are genuinely good enough for all of Week 1. Once you're ready to spend a few dollars (Weeks 4–6 when you're building your actual projects), adding $5–10 to OpenRouter unlocks Claude Sonnet and bumps your daily request limit to 1,000/day. You don't need to do that now.

**Verified free models on OpenRouter as of June 2026 — all support tool calling:**

| Model ID | Notes |
|---|---|
| `openrouter/owl-alpha` | **Start here.** OpenRouter's own model, purpose-built for agentic workloads, native tool use, 1M context. No `:free` suffix needed — it's always free. |
| `openai/gpt-oss-20b:free` | OpenAI open-weight 20B MoE, tool use + structured output, fast, good fallback |
| `google/gemma-4-31b-it:free` | Google Gemma 4, native function calling, 256K context |
| `nvidia/nemotron-3-super-120b-a12b:free` | 120B hybrid MoE, 1M context, built for multi-agent tasks |

**Use `openrouter/owl-alpha` as your primary model.** It's OpenRouter's own model, so it won't be quietly paywalled like `deepseek-chat-v3-0324` was — providers remove their models from the free tier without notice, but OpenRouter controls this one directly.

> **How to verify any model is still free before using it:** go to `https://openrouter.ai/models/<model-id>` (e.g. `https://openrouter.ai/openai/gpt-oss-20b`) and check the pricing shown. If it says `$0/M input tokens $0/M output tokens`, it's free. Do this check whenever a model throws a 404 or payment error — don't assume the doc is still accurate, the free tier changes frequently.

### Python Environment
```bash
python -m venv agents-env
source agents-env/bin/activate  # Windows: agents-env\Scripts\activate
pip install openai tavily-python requests python-dotenv rich pydantic
```

### Project Folder Structure (set this up now, it will grow)
```
week1-agent/
├── .env                   # API keys, never commit this
├── 00_raw_api_call.py     # Phase 0 checkpoint script
├── 01_single_tool.py      # Day 1 exercise
├── 02_multi_tool.py       # Day 2 exercise
├── 03_react_loop.py       # Day 3 exercise
├── 04_error_recovery.py   # Day 4 exercise
├── agent/
│   ├── __init__.py
│   ├── tools.py           # All tool definitions live here
│   ├── loop.py            # The agent loop
│   └── prompts.py         # System prompts
├── outputs/               # Reports written here
└── tests/
    └── test_tools.py      # Unit tests for individual tools
```

---

## The Mental Model to Hold All Week

Every agent interaction, no matter how complex, is this loop:

```
1. You send: [system prompt] + [tool schemas] + [conversation history]
2. Model returns one of two things:
   a. finish_reason = "tool_calls"  → model wants to call a function
   b. finish_reason = "stop"        → model is done, gives final answer
3. If (a): execute the function yourself, append result to history, go to step 1
4. If (b): you have your answer
```

That's it. Everything in Week 1 is a variation of this pattern.

---

## Pre-Reading (Do Before Day 1 — 3–4 hrs)

These are non-negotiable. Read them in order.

**1. Anthropic "Building Effective Agents" post (Dec 2024)**
https://www.anthropic.com/research/building-effective-agents
- This is the canonical reference. Read it once for the big picture, then again slowly and take notes on the five workflow patterns.
- Key mental model to extract: the difference between **workflow** (you control the flow) and **agent** (the model controls the flow).

**2. Anthropic Tool Use — Official Docs (read for concepts, not syntax)**
https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview
- Read: Overview → How tool use works → Define tools → Handle tool calls
- You're using OpenRouter's OpenAI-compatible API, not the Anthropic SDK directly — but the underlying concepts (tool schemas, the request/response cycle, handling tool calls) are identical. Read this for mental model, then use the OpenAI function-calling docs for exact syntax: https://platform.openai.com/docs/guides/function-calling

**3. ReAct Paper — Just the Abstract + Section 2 (20 min)**
https://arxiv.org/abs/2210.03629
- Don't read the whole thing. Read abstract, introduction, and Section 2 (the ReAct formulation). That's enough to understand where the "Think → Act → Observe" pattern comes from.

**4. Anthropic Cookbook — Tool Use Section**
https://github.com/anthropics/anthropic-cookbook/tree/main/patterns/agents
- Clone the repo. Don't run anything yet. Just browse. You'll refer back to specific notebooks during the week.

---

## Day 1 — The API Contract + Your First Tool Call (4 hrs)

**Goal:** Write a complete tool call loop from scratch, no helpers.

### Morning: Understand the Raw API Response (1.5 hrs)

Before writing an agent, you need to be able to read what Claude actually returns. Run this script and study every field of the output:

```python
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
```

**What to look for in the output:**
- `finish_reason: "tool_calls"` vs `"stop"` — this is your branching condition
- `choices[0].message.tool_calls` — list of tool calls, each with `.id`, `.function.name`, `.function.arguments` (a JSON string you must parse)
- `tool_calls[].id` — you must echo this back as `tool_call_id` when returning the result
- `usage` — track `prompt_tokens` vs `completion_tokens`; this is your cost meter

### Afternoon: Build the Full Single-Tool Loop (2.5 hrs)

Now implement the full cycle manually:

```python
# 01_single_tool.py
import os, json
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
            result = eval(tool_input["expression"])
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
```

**Exercise after getting it working:**
1. Print the full `messages` list at the end — study how the conversation history grew
2. Deliberately break the `tool_call_id` echo and observe what happens
3. Ask something that doesn't require a tool — confirm `end_turn` fires on the first pass

---

## Day 2 — Multiple Tools + Tool Selection (4 hrs)

**Goal:** Give the agent 3 tools and watch it decide which one to use (and when to use none).

Now add a web search tool and a text-length counter alongside the calculator. The key learning here is **tool description engineering** — the model picks tools based on the description text you write, so vague descriptions produce wrong selections.

```python
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
```

**Day 2 exercises — test these queries:**
1. `"What is the current price of gold per ounce, and how much would 5kg cost?"` → should use search THEN calculator
2. `"Who won the most recent FIFA World Cup?"` → search only
3. `"What is 15% of 340?"` → calculator only, no search
4. `"Summarize the history of Python"` → no tools at all (general knowledge)

For each one, log which tool(s) were called. If the wrong tool fires, fix the description.

**Key concept to internalize:** The description is the model's only guide for tool selection. It is prompt engineering on a schema.

---

## Day 3 — The Full ReAct Loop + System Prompt Engineering (4 hrs)

**Goal:** Implement the proper ReAct pattern with explicit Thought → Action → Observation traces, and engineer a system prompt that produces consistent, structured behavior.

### What ReAct Looks Like in Your Conversation History

```
User:      Research and explain why Python became dominant in ML
Assistant: [content: "I'll research this systematically. Let me start with..."]
           [tool_calls: web_search("Python ML dominance history")]
Tool:      [tool_call_id: "...", content: "... search results ..."]
Assistant: [content: "Good. Now let me look at adoption statistics..."]
           [tool_calls: web_search("Python ML adoption statistics 2024")]
Tool:      [tool_call_id: "...", content: "..."]
Assistant: [content: "Based on my research, Python became dominant because..."]
           ← finish_reason = "stop", no more tool_calls
```

The model's text blocks between tool calls are its "thoughts" — explicit reasoning about what it learned and what to do next. Your system prompt needs to encourage this.

### System Prompt for a Research Agent

```python
# agent/prompts.py

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
```

### Build the Full Loop with Logging

```python
# 03_react_loop.py
import os, json
from openai import OpenAI
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from agent.tools import TOOL_DEFINITIONS, execute_tool
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
                
                result = execute_tool(tc.function.name, tool_input)
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
    Path("outputs").mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"outputs/report_{timestamp}.md"
    
    with open(filename, "w") as f:
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
```

**Test queries for Day 3:**
- `"What are the main technical differences between transformer and Mamba architectures, and what are the practical tradeoffs?"` — requires 4–6 searches, tests synthesis
- `"What is the current state of Pakistan's tech startup ecosystem?"` — tests local/regional search depth
- `"How does retrieval-augmented generation work and what are its failure modes?"` — partially in model's knowledge, should still search for recent work

---

## Day 4 — Error Handling + Graceful Degradation (3 hrs)

**Goal:** Your agent must not crash when a tool fails. It should tell the model what went wrong and let the model adapt.

This is the most underrated skill in agent development. A tool can fail because: the API is down, the query returned nothing, the result is malformed, or you hit a rate limit.

```python
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
            # ... format results ...
            
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
```

**Day 4 exercises — inject failures on purpose:**
1. Pass an intentionally bad expression to calculator (`"847 */ 23"`) — confirm model sees the error and recovers
2. Temporarily set a wrong Tavily API key — confirm model handles the search failure gracefully
3. Return empty string from web search — confirm model tries a rephrased query

---

## Day 5–6 — Build the Full Research Report Agent (6 hrs)

Now assemble everything into the actual project. The agent should:

1. Accept a research topic
2. **Plan** (generate a structured research plan before any tool call)
3. **Execute** iterative searches (minimum 4, guided by the plan)
4. **Optionally calculate** if numerical analysis is needed
5. **Write** a cited markdown report with proper sections
6. **Self-evaluate** (one final loop where it checks: are all claims sourced? is anything missing? is the report well-structured?)

The self-evaluation is the stretch goal — implement it as a second model call after the research is done, with the report as input and a rubric as the system prompt. It returns a list of issues, you show the issues to the main agent, and it revises.

### Suggested Research Topics to Test Against
- `"Explain how the attention mechanism works, with focus on computational complexity and recent efficiency improvements like FlashAttention"`
- `"What are the current open-source alternatives to GPT-4 and how do they compare on coding benchmarks?"`
- `"How do AI agent memory systems work in production — what are the state of the art approaches?"` ← meta, and gives you reading material for Week 3

---

## Day 7 — Reflection + Hardening (2 hrs)

**Don't skip this.** A pattern many learners miss: the code works but you don't know *why*. Use Day 7 to make it concrete.

### Questions to answer in writing (put them in a `REFLECTIONS.md`):

1. **Draw the message history** for one of your completed runs. Show every `role: user` and `role: assistant` turn, including tool results. What is the model "seeing" at each step?

2. **What happens if the model never calls `end_turn`?** How does your `max_iterations` guard prevent infinite loops, and what should you return to the user when it triggers?

3. **Redesign the tool descriptions.** Take your current `web_search` description, rewrite it to be deliberately vague, run the same queries, and document which ones break. Then fix it and document the difference. This teaches you how much tool behavior lives in the description.

4. **Token cost audit.** Run your three best test queries. Log `prompt_tokens` and `completion_tokens` from `response.usage`. Free-tier models cost $0 — but note the total token count anyway, because when you eventually move to paid models (Sonnet, GPT-4o), you'll want to know how token-heavy your agent is before the bill arrives. Estimate what the same runs would cost on DeepSeek V3 paid vs Claude Sonnet.

5. **What is one thing your agent does wrong that isn't a code bug — it's a prompt problem?** Identify it, fix the system prompt, verify the fix.

---

## Resources Reference Card

### Official docs (free, authoritative)
| Resource | URL |
|---|---|
| OpenAI Function Calling docs (your actual API syntax) | https://platform.openai.com/docs/guides/function-calling |
| OpenRouter models list (filter by :free) | https://openrouter.ai/models/?q=free |
| Anthropic Cookbook — Agents patterns (concepts) | https://github.com/anthropics/anthropic-cookbook/tree/main/patterns/agents |
| Anthropic — Building Effective Agents | https://www.anthropic.com/research/building-effective-agents |
| ReAct paper (skim sec 1–2 only) | https://arxiv.org/abs/2210.03629 |
| Tavily docs | https://docs.tavily.com |

### Free search APIs for your agent
| API | Free tier | Best for |
|---|---|---|
| Tavily | 1,000/month | LLM-optimized results, recommended for Week 1 |
| Serper | 2,500/month | Raw Google SERP if Tavily credits run out |

### No paid resources required this week. Everything above is free.

---

## End-of-Week Checklist

Before moving to Week 2, you should be able to answer **yes** to all of these:

- [ ] I can explain what `finish_reason: "tool_calls"` means and exactly what you must send back
- [ ] I can draw the full multi-turn message history of a 3-tool-call agent run from memory
- [ ] I understand why `tool_call_id` must be echoed and what breaks if you don't
- [ ] I can write a tool description that guides correct tool selection
- [ ] My agent handles tool errors without crashing — the model knows what went wrong
- [ ] I have a working `max_iterations` guard and understand why it's necessary
- [ ] I can read token usage and estimate cost for a run
- [ ] My Research Report Agent produces a cited markdown report on arbitrary topics
- [ ] I have a `REFLECTIONS.md` with answers to the Day 7 questions

If you can't check all of these, don't move to Week 2. Go back to the specific day that introduced that concept and re-do the exercise.

---

## What Week 2 Builds On This

Week 2 adds a code-execution tool (giving the agent a Python interpreter as a tool) and sandboxing. Every concept from this week transfers directly — same loop, same error handling pattern, same message history structure. The only new thing is the tool itself and the safety logic around it.
