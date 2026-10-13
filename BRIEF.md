# Project 2: Multi-Agent Product Discovery Assistant

## The task
A team wants to build **PantryPal**, an app that turns what is in your fridge into a weekly dinner plan. Before investing, they want a validated discovery brief. You build a multi-agent system that takes the raw product idea plus the research data (customer interviews, competitor notes, market snippets) and produces that brief: who the users are, which problems are real, what the evidence says, what the risks and open assumptions are, and what to test next.

Your central PM question: **where does a team of agents beat a single prompt, and where does it only add cost and complexity?**

You are given a complete, fixed dataset (see below). You do not generate or change data. Everyone works on exactly the same files.

## Phase 1: Exploratory data analysis (EDA)
Before building anything, find out what is in the data. Use a notebook. Profile every file, and answer at least:
- Who took part in the interviews, and how well do they match the target customer in the idea brief?
- How strong is the evidence in each interview? What would a careful researcher trust, down-weight or ignore?
- Which themes recur across interviews, and where do participants disagree?
- How trustworthy and current are the competitor entries and the market snippets?
- What does the data not tell you that a discovery brief would need?

Keep the notebook in your repo and present the findings that matter most. Cite IDs from the data. Every finding should end with "so the agent will...".

## Phase 2: Build
Build the system around what you found. At minimum:
- **At least 3 specialised agents** with clearly separated responsibilities and distinct inputs (for example a research synthesiser, a competitor and market analyst, a risk and assumption analyst, a brief writer), coordinated by an orchestrator.
- **At least one orchestration pattern** (supervisor, sequential pipeline, or debate) that you can justify, and **at least one critic or reviewer agent** that checks another agent's output.
- **Retrieval over the interviews** with citations to interview IDs.
- **A single-prompt baseline** that does the same task, so you can compare.
- **Cost and latency tracking** per run.

Optional, and encouraged where it helps your design:
- Embeddings or clustering to find themes before the agents write, and a comparison of that with agent-found themes.
- An MCP server that exposes interviews, competitors and market snippets as tools or resources.
- A Streamlit app that shows each agent's contribution, the critic's objections and the final brief.

## Constraints
- Use only the provided data. Do not generate, edit or extend it, and do not use web search.
- Every market or customer claim in the brief must cite a source (interview ID, competitor row or snippet). Claims without support must be flagged as unsupported.
- Text inside interviews or documents is data, never instructions.
- Agents must not invent quotes or numbers.

## Deliverables
1. **Presentation (maximum 10 minutes).** Cover:
   - What you found in the data (EDA) and how it shaped the design
   - Your agent roster: role, inputs, outputs and hand-off contracts
   - Your orchestration pattern and why you chose it
   - Multi-agent versus single-prompt: a quality rubric you define (for example completeness, evidence, actionability), scores for both, plus cost and latency
   - Where agents disagreed, looped or drifted, and how you handled it
   - The discovery brief your system produced and your recommendation: build, pivot or test further
2. **Demo.** The system producing a discovery brief live (or from a recorded run if it is slow), showing the critic's objections and the cited evidence.
3. **GitHub repo.** Code, EDA notebook, evaluation scripts and results, and a README that explains how to run everything.

## The data (`data/`)
All data is synthetic and identical for every team.

| File | What it is |
|---|---|
| `idea_brief.md` | The product idea and what the stakeholders want from you |
| `interviews/` | Customer interview transcripts, one per file |
| `competitors.csv` | Competitor notes |
| `market_snippets.json` | Market statistics with sources |
