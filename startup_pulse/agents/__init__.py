from startup_pulse.agents.news import NewsAgent
from startup_pulse.agents.papers import PapersAgent
from startup_pulse.agents.grants import GrantsAgent
from startup_pulse.agents.funding import FundingAgent
from startup_pulse.agents.github import GitHubAgent

ALL_AGENTS = {
    "news": NewsAgent,
    "papers": PapersAgent,
    "grants": GrantsAgent,
    "funding": FundingAgent,
    "github": GitHubAgent,
}

COLLECTIBLE_AGENTS = ALL_AGENTS
