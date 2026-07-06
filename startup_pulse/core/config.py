import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# RSS Feed Sources — AI News (Tier 1 & Tier 2, no research-only feeds)
# ---------------------------------------------------------------------------
NEWS_FEEDS = {
    # Tier 1 — Company blogs
    "MIT Technology Review AI": "https://www.technologyreview.com/topic/artificial-intelligence/feed",
    "OpenAI Blog": "https://openai.com/blog/rss.xml",
    "Google AI Blog": "https://blog.google/technology/ai/rss/",
    "Anthropic Blog": "https://www.anthropic.com/rss.xml",
    "DeepMind Blog": "https://deepmind.google/blog/rss.xml",
    "NVIDIA AI Blog": "https://blogs.nvidia.com/blog/category/deep-learning/feed/",
    "Microsoft AI Blog": "https://blogs.microsoft.com/ai/feed/",
    "The Verge AI": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    # Tier 2 — Tech media
    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "VentureBeat AI": "https://venturebeat.com/category/ai/feed/",
}

# ---------------------------------------------------------------------------
# Research Paper Sources
# ---------------------------------------------------------------------------
PAPER_FEEDS = {
    # arXiv categories
    "arXiv cs.AI": "https://rss.arxiv.org/rss/cs.AI",
    "arXiv cs.LG": "https://rss.arxiv.org/rss/cs.LG",
    "arXiv cs.CL": "https://rss.arxiv.org/rss/cs.CL",
    "arXiv cs.CV": "https://rss.arxiv.org/rss/cs.CV",
    "arXiv cs.NE": "https://rss.arxiv.org/rss/cs.NE",
    "arXiv cs.RO": "https://rss.arxiv.org/rss/cs.RO",
    "arXiv stat.ML": "https://rss.arxiv.org/rss/stat.ML",
    # Aggregators
    "Hugging Face Papers": "https://huggingface.co/papers/rss",
    "Papers With Code": "https://paperswithcode.com/latest/rss",
}

# ---------------------------------------------------------------------------
# Grant & Scheme Sources (scraped)
# ---------------------------------------------------------------------------
GRANT_SOURCES = [
    # Central Government
    {"name": "Startup India", "url": "https://www.startupindia.gov.in/content/sih/en/government-schemes.html", "region": "Central"},
    {"name": "MEITY Schemes", "url": "https://www.meity.gov.in/schemes", "region": "Central"},
    {"name": "DST Call for Proposals", "url": "https://dst.gov.in/call-for-proposals", "region": "Central"},
    {"name": "MSME Schemes", "url": "https://msme.gov.in/all-schemes", "region": "Central"},
    {"name": "BIRAC", "url": "https://birac.nic.in/cfp.php", "region": "Central"},
    # Telangana
    {"name": "T-Hub", "url": "https://www.t-hub.co/", "region": "Telangana"},
    {"name": "WE-Hub", "url": "https://wehub.telangana.gov.in/", "region": "Telangana"},
    {"name": "Telangana IT", "url": "https://it.telangana.gov.in/", "region": "Telangana"},
    # Andhra Pradesh
    {"name": "AP Innovation Society", "url": "https://apis.ap.gov.in/", "region": "Andhra Pradesh"},
    {"name": "APIIC", "url": "https://apiic.ap.gov.in/", "region": "Andhra Pradesh"},
    # Institutional
    {"name": "IIIT-H CIE", "url": "https://cie.iiit.ac.in/", "region": "Institutional"},
    {"name": "iHub-Data IIIT-H", "url": "https://ihub-data.iiit.ac.in/", "region": "Institutional"},
]

# ---------------------------------------------------------------------------
# Funding Opportunity Sources (scraped)
# ---------------------------------------------------------------------------
FUNDING_SOURCES = [
    {"name": "Y Combinator", "url": "https://www.ycombinator.com/apply/", "type": "accelerator"},
    {"name": "Antler India", "url": "https://www.antler.co/location/india", "type": "pre-seed"},
    {"name": "100X.VC", "url": "https://www.100x.vc/", "type": "pre-seed"},
    {"name": "T-Hub Programs", "url": "https://www.t-hub.co/", "type": "accelerator"},
    {"name": "Indian Angel Network", "url": "https://www.indianangelnetwork.com/", "type": "seed"},
    {"name": "Better Capital", "url": "https://bettercapital.vc/", "type": "pre-seed"},
    {"name": "Techstars India", "url": "https://www.techstars.com/accelerators", "type": "accelerator"},
]

# ---------------------------------------------------------------------------
# GitHub Trending
# ---------------------------------------------------------------------------
GITHUB_TRENDING_URL = "https://github.com/trending"

# ---------------------------------------------------------------------------
# Keywords
# ---------------------------------------------------------------------------
CONFERENCE_KEYWORDS = [
    "neurips", "nips", "icml", "iclr", "cvpr", "iccv", "eccv",
    "acl", "emnlp", "naacl", "aaai", "ijcai", "kdd", "sigir",
    "sigmod", "vldb", "icde", "www", "cikm", "wsdm", "recsys",
    "uai", "aistats", "colt", "icra", "iros", "corl",
]

AI_KEYWORDS = [
    "ai", "artificial intelligence", "machine learning", "deep learning",
    "neural network", "llm", "large language model", "gpt", "chatgpt",
    "claude", "gemini", "transformer", "diffusion", "generative",
    "openai", "anthropic", "deepmind", "midjourney", "stable diffusion",
    "computer vision", "nlp", "natural language processing",
    "reinforcement learning", "robotics", "autonomous",
]

PAPER_KEYWORDS = AI_KEYWORDS + [
    "rag", "retrieval augmented", "fine-tuning", "rlhf", "dpo",
    "mixture of experts", "moe", "vision language model", "vlm",
    "multimodal", "attention mechanism", "embedding", "vector database",
    "agentic", "chain of thought", "reasoning",
]

# ---------------------------------------------------------------------------
# Email Configuration
# ---------------------------------------------------------------------------
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", "")

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# ---------------------------------------------------------------------------
# News tier mapping (tier 1 sources sort first in digest)
# ---------------------------------------------------------------------------
NEWS_TIER1 = {
    "MIT Technology Review AI", "OpenAI Blog", "Google AI Blog",
    "Anthropic Blog", "DeepMind Blog", "NVIDIA AI Blog",
    "Microsoft AI Blog", "The Verge AI",
}

# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
STORAGE_RETENTION_DAYS = 7
