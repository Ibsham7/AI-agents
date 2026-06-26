# AI Agents Learning Repo

This repository collects the current implementations from Week 1 and Week 2 of an agent-building learning path. Week 1 focuses on tool use and research loops. Week 2 expands into persistent analysis, code review, and safe local execution.

## Repository Layout

```text
week1-agent/
  00_raw_api_call.py
  01_single_tool.py
  02_multi_tool.py
  03_react_loop.py
  Research_Agent.py
  agent/
  tests/
  outputs/

week2-agent/
  data.py
  agents/
  tools/
  sandbox/
  test_targets/
  datasets/
  outputs/
```

## Week 1: Tool Use Foundations

Week 1 shows the progression from a plain model call to a multi-step research agent.

- `00_raw_api_call.py` demonstrates a basic OpenRouter chat completion, then adds a single calculator tool call and manually returns the tool result to the model.
- `01_single_tool.py` wraps that pattern into a reusable loop with one calculator tool.
- `02_multi_tool.py` adds a small tool suite: web search, calculator, and word counting.
- `03_react_loop.py` turns the tool loop into a research agent that logs thoughts, tool calls, token usage, and duration.
- `Research_Agent.py` is the more complete research-agent version with safe tool execution and markdown report generation.

Week 1 outputs are written under `week1-agent/outputs/`.

## Week 2: Analysis And Review Agents

Week 2 adds two more practical agent workflows.

### Data Analyst Agent

`week2-agent/agents/data_analyst.py` runs a persistent analysis session for CSV files. It can:

- inspect a dataset with `describe_csv`
- execute analysis code in a persistent namespace
- keep variables in scope across turns
- reset the session when switching datasets

The supporting pieces are:

- `week2-agent/tools/analysis_tools.py` for dataset inspection
- `week2-agent/tools/Schemas.py` for tool definitions
- `week2-agent/sandbox/namespace.py` for the persistent execution state
- `week2-agent/sandbox/executor.py` for isolated Python execution and blocked imports

Charts are saved under `week2-agent/outputs/charts/`.

### Code Review Agent

`week2-agent/agents/code_review.py` performs a structured Python code review. It can:

- list directories once and cache repeated directory reads
- read files, run lint checks, measure complexity, and execute reproduction snippets
- write the final review report to `week2-agent/outputs/reviews/`

The review workflow is driven by:

- `week2-agent/tools/file_tools.py`
- `week2-agent/tools/execution_tools.py`
- `week2-agent/tools/Schemas.py`
- `week2-agent/agents/prompts.py`

## Setup

1. Create and activate a virtual environment.
2. Install the packages for the week you want to run.
3. Set the required API keys in `.env`.

### Week 1 Dependencies

```bash
pip install openai python-dotenv tavily-python
```

### Week 2 Dependencies

```bash
pip install -r week2-agent/requirement.txt
```

### Environment Variables

```bash
OPENROUTER_API_KEY=your_openrouter_key
TAVILY_API_KEY=your_tavily_key
```

Week 1 uses both `OPENROUTER_API_KEY` and `TAVILY_API_KEY`. Week 2 primarily uses `OPENROUTER_API_KEY`.

## Run Examples

Run from the repository root.

### Week 1

```bash
python week1-agent/00_raw_api_call.py
python week1-agent/01_single_tool.py
python week1-agent/02_multi_tool.py
python week1-agent/03_react_loop.py
python week1-agent/Research_Agent.py
```

### Week 2

```bash
python week2-agent/data.py
python week2-agent/agents/data_analyst.py
python week2-agent/agents/code_review.py week2-agent/test_targets/
```

## Outputs

- `week1-agent/outputs/` stores research traces and agent logs.
- `week2-agent/outputs/charts/` stores generated visualizations.
- `week2-agent/outputs/reviews/` stores code review reports.

## Notes

- The Week 2 execution sandbox blocks risky imports such as `subprocess`, `socket`, `requests`, and `urllib`.
- `week2-agent/data.py` can regenerate the sample `sales.csv` and `students.csv` datasets.
- The repo is still organized as a learning workspace, so some files are stepping stones rather than polished production entry points.