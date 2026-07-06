import time
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from startup_pulse.core import config, storage
from startup_pulse.agents.base import BaseAgent

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
TIMEOUT = 15

# Only keep links that strongly indicate an active funding/program opportunity
STRONG_INDICATORS = [
    "apply", "application", "program", "programme", "batch",
    "cohort", "accelerator", "incubat", "seed fund", "pre-seed",
    "fellowship", "pitch", "demo day", "open call",
    "invest", "funding round",
]

NOISE_WORDS = [
    "login", "sign up", "register", "contact", "about", "home",
    "faq", "terms", "privacy", "disclaimer", "sitemap", "feedback",
    "twitter", "facebook", "linkedin", "instagram", "youtube",
    "blog", "news", "media", "gallery", "photo", "video",
    "press release", "cookie", "subscribe", "newsletter",
    "read more", "learn more", "view all", "know more", "click here",
    "portfolio", "team", "mentor", "alumni", "partner",
    "career", "job", "hiring",
]


class FundingAgent(BaseAgent):
    """Tracks pre-seed, seed, and accelerator funding opportunities."""

    def get_agent_name(self) -> str:
        return "funding"

    def collect(self) -> int:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] FundingAgent: starting collection...")
        total_new = 0
        for source in config.FUNDING_SOURCES:
            items = self._scrape_source(source)
            if items:
                added = self.add_items(items)
                total_new += added
                print(f"  {source['name']}: {len(items)} found, {added} new")
            else:
                print(f"  {source['name']}: 0 found")
            time.sleep(2)

        storage.cleanup_old_files("funding")
        print(f"FundingAgent: {total_new} new funding opportunities added.")
        return total_new

    def _scrape_source(self, source: dict) -> list[dict]:
        name = source["name"]
        url = source["url"]
        funding_type = source["type"]
        try:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            resp.raise_for_status()
        except Exception as e:
            print(f"  Error fetching {name}: {e}")
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        items = []
        base = urlparse(url)

        for a_tag in soup.find_all("a", href=True):
            text = a_tag.get_text(strip=True)
            href = a_tag["href"]
            if not text or len(text) < 15 or len(text) > 200:
                continue

            if not href.startswith("http"):
                if href.startswith("/"):
                    href = f"{base.scheme}://{base.netloc}{href}"
                else:
                    continue

            text_lower = text.lower()

            # Skip noise
            if any(w in text_lower for w in NOISE_WORDS):
                continue

            # Only keep strong matches
            if not any(w in text_lower for w in STRONG_INDICATORS):
                continue

            parent = a_tag.parent
            summary = parent.get_text(strip=True)[:250] if parent else ""

            items.append({
                "title": text,
                "link": href,
                "summary": summary if summary != text else "",
                "source": name,
                "type": funding_type,
                "deadline": None,
                "published": datetime.now(timezone.utc).isoformat(),
            })

        seen_links = set()
        seen_titles = set()
        unique = []
        for item in items:
            norm_title = item["title"].lower().strip()
            if item["link"] in seen_links or norm_title in seen_titles:
                continue
            seen_links.add(item["link"])
            seen_titles.add(norm_title)
            unique.append(item)

        return unique[:8]  # Cap at 8 per source
