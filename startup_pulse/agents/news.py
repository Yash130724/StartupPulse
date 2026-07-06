import time
from datetime import datetime, timedelta, timezone

import feedparser

from startup_pulse.core import config, storage
from startup_pulse.agents.base import BaseAgent


class NewsAgent(BaseAgent):
    """Collects AI news from top-tier RSS feeds."""

    def get_agent_name(self) -> str:
        return "news"

    def collect(self) -> int:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] NewsAgent: starting collection...")
        total_new = 0
        for name, url in config.NEWS_FEEDS.items():
            articles = self._fetch_feed(name, url)
            if articles:
                added = self.add_items(articles)
                total_new += added
                print(f"  {name}: {len(articles)} fetched, {added} new")
            else:
                print(f"  {name}: 0 fetched")
            time.sleep(1)

        storage.cleanup_old_files("news")
        print(f"NewsAgent: {total_new} new articles added.")
        return total_new

    @staticmethod
    def _parse_published(entry) -> datetime | None:
        for attr in ("published_parsed", "updated_parsed"):
            parsed = getattr(entry, attr, None)
            if parsed:
                try:
                    return datetime(*parsed[:6], tzinfo=timezone.utc)
                except Exception:
                    continue
        return None

    def _fetch_feed(self, name: str, url: str) -> list[dict]:
        try:
            feed = feedparser.parse(url)
        except Exception as e:
            print(f"  Error fetching {name}: {e}")
            return []

        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        articles = []

        for entry in feed.entries:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            summary = entry.get("summary", entry.get("description", "")).strip()
            if not title or not link:
                continue

            published = self._parse_published(entry)
            if published and published < cutoff:
                continue

            if len(summary) > 500:
                summary = summary[:497] + "..."

            articles.append({
                "title": title,
                "link": link,
                "summary": summary,
                "published": published.isoformat() if published else datetime.now(timezone.utc).isoformat(),
                "source": name,
            })

        return articles
