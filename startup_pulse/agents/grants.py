import re
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

# Words that indicate the link is a real scheme/grant, not navigation noise
STRONG_INDICATORS = [
    "scheme", "grant", "fund scheme", "seed fund", "subsidy", "incentive scheme",
    "call for proposal", "call for application", "apply now", "open for application",
    "credit guarantee", "equity support", "interest subvention",
    "incubation program", "accelerator program", "fellowship",
]

# Words that indicate navigation/generic pages to skip
NOISE_WORDS = [
    "login", "sign up", "register", "contact us", "about us", "home",
    "faq", "terms", "privacy", "disclaimer", "sitemap", "feedback",
    "download app", "play store", "app store", "twitter", "facebook",
    "linkedin", "instagram", "youtube", "blog", "news", "media",
    "gallery", "photo", "video", "annual report", "press release",
    "logo", "certificate", "modify certificate", "access/modify",
    "regulatory support", "playbook", "guide", "handbook", "manual",
    "know more", "read more", "click here", "learn more", "view all",
    "explore", "menu", "navigation", "cookie",
]

# Patterns that suggest an expired or date-passed deadline
EXPIRED_PATTERNS = [
    r"closed", r"expired", r"deadline\s*:\s*\d{1,2}[/-]\d{1,2}[/-](2024|2023|2022|2021|2020)",
    r"last date.*?(2024|2023|2022|2021|2020)",
]


class GrantsAgent(BaseAgent):
    """Scrapes government and institutional portals for active grant/scheme opportunities."""

    def get_agent_name(self) -> str:
        return "grants"

    def collect(self) -> int:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] GrantsAgent: starting collection...")
        total_new = 0
        for source in config.GRANT_SOURCES:
            items = self._scrape_source(source)
            if items:
                added = self.add_items(items)
                total_new += added
                print(f"  {source['name']}: {len(items)} found, {added} new")
            else:
                print(f"  {source['name']}: 0 found")
            time.sleep(2)

        storage.cleanup_old_files("grants")
        print(f"GrantsAgent: {total_new} new grants added.")
        return total_new

    @staticmethod
    def _is_noise(text: str) -> bool:
        t = text.lower()
        if any(w in t for w in NOISE_WORDS):
            return True
        if len(text.split()) < 3:
            return True
        return False

    @staticmethod
    def _is_strong_match(text: str) -> bool:
        t = text.lower()
        return any(w in t for w in STRONG_INDICATORS)

    @staticmethod
    def _looks_expired(text: str) -> bool:
        t = text.lower()
        for pat in EXPIRED_PATTERNS:
            if re.search(pat, t):
                return True
        return False

    def _scrape_source(self, source: dict) -> list[dict]:
        name = source["name"]
        url = source["url"]
        region = source["region"]
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

            # Build absolute URL
            if not href.startswith("http"):
                if href.startswith("/"):
                    href = f"{base.scheme}://{base.netloc}{href}"
                else:
                    continue

            # Skip obvious noise
            if self._is_noise(text):
                continue

            # Only keep if it looks like a real scheme/grant
            if not self._is_strong_match(text):
                continue

            # Get surrounding context for summary
            parent = a_tag.parent
            context = parent.get_text(strip=True)[:250] if parent else ""

            # Skip if context suggests expired
            if self._looks_expired(context):
                continue

            items.append({
                "title": text,
                "link": href,
                "summary": context if context != text else "",
                "source": name,
                "region": region,
                "published": datetime.now(timezone.utc).isoformat(),
                "deadline": None,
            })

        # Dedup within this scrape by link and by normalized title
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

        return unique[:10]  # Hard cap: only top 10 per source
