"""Phase 2 agents. Each module owns one role: its prompt, its inputs and its output contract.

    research   Research synthesiser   interviews (via retrieval) -> ResearchSynthesis
    market     Competitor/market      competitor rows, snippets   -> MarketAnalysis
    risk       Risk and assumptions   both analyses, EDA gaps     -> RiskAnalysis
    writer     Brief writer           all three analyses          -> DiscoveryBrief
    critic     Critic                 draft + sources (via tools) -> Critique
"""
