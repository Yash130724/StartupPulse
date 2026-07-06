import re
import time
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

from startup_pulse.core import config, storage
from startup_pulse.agents.base import BaseAgent

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
TIMEOUT = 15


class GitHubAgent(BaseAgent):
    """Fetches GitHub trending repos."""

    def get_agent_name(self) -> str:
        return "github"

    def collect(self) -> int:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] GitHubAgent: starting collection...")
        total_new = 0

        for label, url in [
            ("GitHub Trending Daily", config.GITHUB_TRENDING_URL),
            ("GitHub Trending Weekly", config.GITHUB_TRENDING_URL + "?since=weekly"),
        ]:
            repos = self._scrape_trending(url, label)
            if repos:
                added = self.add_items(repos)
                total_new += added
                print(f"  {label}: {len(repos)} found, {added} new")
            else:
                print(f"  {label}: 0 found")
            time.sleep(2)

        storage.cleanup_old_files("github")
        print(f"GitHubAgent: {total_new} new repos added.")
        return total_new

    def _scrape_trending(self, url: str, label: str) -> list[dict]:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            resp.raise_for_status()
        except Exception as e:
            print(f"  Error fetching {label}: {e}")
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        repos = []

        for article in soup.select("article.Box-row"):
            # Repo name (owner/repo)
            h2 = article.select_one("h2 a")
            if not h2:
                continue
            repo_name = h2.get_text(strip=True).replace(" ", "").replace("\n", "")
            link = "https://github.com" + h2["href"]

            # Description
            p = article.select_one("p")
            description = p.get_text(strip=True) if p else ""

            # Language
            lang_span = article.select_one("[itemprop='programmingLanguage']")
            language = lang_span.get_text(strip=True) if lang_span else ""

            # Stars
            stars = 0
            stars_today = 0
            star_links = article.select("a.Link--muted")
            if star_links:
                star_text = star_links[0].get_text(strip=True).replace(",", "")
                try:
                    stars = int(star_text)
                except ValueError:
                    pass

            # Stars today
            spans = article.select("span.d-inline-block")
            for span in spans:
                text = span.get_text(strip=True)
                match = re.search(r"([\d,]+)\s+stars?\s+today", text, re.IGNORECASE)
                if not match:
                    match = re.search(r"([\d,]+)\s+stars?\s+this\s+week", text, re.IGNORECASE)
                if match:
                    try:
                        stars_today = int(match.group(1).replace(",", ""))
                    except ValueError:
                        pass

            repos.append({
                "name": repo_name,
                "link": link,
                "description": description[:300],
                "language": language,
                "stars": stars,
                "stars_today": stars_today,
                "source": label,
                "published": datetime.now(timezone.utc).isoformat(),
            })

        return repos
