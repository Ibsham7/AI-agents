# Agentic AI Learning Roadmap — Intensive Track (20+ hrs/week)

**Total duration:** ~8 weeks
**Starting point:** BS AI, 4th semester, solid ML/MLOps/web dev, basic LLM knowledge
**Philosophy:** Build the agent loop by hand before touching a framework. Frameworks should feel like "oh, that's just automating what I already understand," not magic.

---

## Phase 0 — LLM & Agent Fundamentals (Days 1–3, ~15–20 hrs)

You already know ML, so skip training internals and go straight for inference-time mechanics.

**Concepts to nail:**
- Autoregressive token prediction, context windows, temperature/sampling — just enough to reason about behavior, not the math
- Prompting fundamentals: zero-shot vs few-shot, chain-of-thought, system vs user prompts
- Structured output (forcing JSON/schema-conformant responses)
- **Tool/function calling** — how the model emits a structured "intent to call a function," your code executes it, and you feed the result back in
- The **ReAct pattern** (Reason → Act → Observe → repeat) — almost every agent, no matter how fancy, is this loop underneath

**Resources:**
- Anthropic's engineering blog post *"Building Effective Agents"* — read this first, it's the best mental model in existence right now
- Anthropic prompt engineering docs (docs.claude.com)
- Anthropic API docs — Tool Use section
- ReAct paper (Yao et al., 2022) — skim, don't chase the math

**Checkpoint (no real project yet):** write a raw Python script that calls the Claude API with one tool (e.g. a calculator function) and completes a full call → execute → respond loop *manually*, no framework.

---

## Week 1 — Tool-Calling Agent From Scratch

**Concepts:** building the agent loop yourself in raw Python — tool schema design, parsing tool calls, multi-turn loop management, handling the model calling a tool wrong (it will)

**Project: Research Report Agent**
Query → web search tool → reads sources → writes a cited synthesis report.

**Stretch goal:** add a second tool (e.g. a calculator or file-write tool) to see how the model handles tool *selection*, not just tool *use*.

---

## Week 2 — Code-Execution Agents & Sandboxing

**Concepts:** giving an agent a code-execution tool, sandboxing/safety boundaries, repairing model-generated code, treating execution errors as feedback the model can act on

**Projects (back-to-back, ~3–4 days each at your pace):**
- **Code Review Agent** — reads a repo/file, finds bugs, suggests fixes, runs the test suite
- **Data Analyst Agent** — given a CSV, writes/executes pandas on the fly, generates charts on request

**Tip:** look at how Claude Code structures its tool definitions (read the docs, not source) for inspiration on clean tool design.

---

## Week 3 — Memory & RAG

**Concepts:** embeddings (fast for you, you know ML), vector stores (start with Chroma — local, zero setup friction), chunking strategy (the actual hard part of RAG), short-term vs long-term memory, and knowing *when RAG is the wrong tool*

**Project — pick one:**
- **Personalized Study Buddy** — RAG over your own course PDFs, generates quizzes, tracks weak topics over time
- **Expense/Receipt Tracker Agent** — parses receipts, categorizes spend, remembers patterns, answers natural-language questions about your finances over time

**Resource:** Anthropic's "Contextual Retrieval" blog post

---

## Week 4–5 — Multi-Agent Orchestration: Recruitment Agent

This is your first original idea — now that the fundamentals are solid, build it properly.

**Concepts:** orchestration patterns (sequential pipeline, supervisor/worker, parallel fan-out), structured handoffs between agents, enforcing schema'd output (Pydantic), human-in-the-loop checkpoints. Introduce **LangGraph** here — it keeps you close to the graph/loop you already understand, unlike higher-abstraction frameworks.

**Project: Recruitment Agent**
CV parser → JD-matcher/screener → interview-question generator → interview conductor → evaluator/scorer → scheduler.

**Important design note:** put a human-approval gate before final candidate selection. This isn't just good engineering — fully autonomous hiring decisions carry real bias and compliance risk. Building that gate in is a legitimate design skill, not a cop-out.

---

## Week 6 — Multi-Agent Orchestration: Social Media Manager

Your second original idea. You'll move faster here since you're reusing orchestration patterns from week 4–5.

**Concepts:** feedback loops (an analytics agent feeding results back into content strategy), scheduled/autonomous agent triggers, content approval workflows

**Project: Social Media Manager Agent**
Trend-research agent → content writer agent → visuals agent → scheduler agent → performance-analyst agent that closes the loop back into future content decisions.

---

## Week 7 — Evaluation & Observability

This is where your MLOps background stops being "nice to have" and becomes a real differentiator — most agent-tutorial students skip this entirely.

**Concepts:** tracing every tool call (latency, token cost, success/failure), LLM-as-judge evaluation, building eval datasets, catching regressions when prompts change, why "vibes-based" agent development collapses in production

**Project:** build a lightweight eval/observability layer (your own mini LangSmith) and retrofit it onto both the Recruitment Agent and Social Media Manager — instrument both, write 15–20 eval cases each, track results on a small dashboard.

---

## Week 8 — Productionizing & Portfolio Packaging

**Concepts:** deployment (FastAPI backend + Docker), basic CI/CD for prompts/agents, cost monitoring

**Deliverable:** polish 2–3 of your projects into actual portfolio pieces:
- Clean README with architecture diagram
- Short demo video/GIF
- A short write-up explaining your design decisions (orchestration choices, why you added the human-approval gate, what broke and how you fixed it)

This matters a lot right now — agent-building portfolios with real eval/observability work are rare even among working engineers.

---

## Ground Rules for This Roadmap

1. **Don't skip Phase 0.** Everything after it assumes you've built one tool-calling loop by hand.
2. **Frameworks come after, not before, the fundamentals.** You'll get far more out of LangGraph in Week 4 having already built a loop manually than if you started there.
3. **Each week has a real working project at the end of it** — not a tutorial follow-along. If you finish early, add a stretch goal rather than moving on; depth here compounds.
4. **Weeks 4–6 are your original ideas** — everything before them exists to make those two builds smooth instead of painful.
