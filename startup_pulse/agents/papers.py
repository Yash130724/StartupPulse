import re
import time
from datetime import datetime, timedelta, timezone

import feedparser

from startup_pulse.core import config, storage
from startup_pulse.agents.base import BaseAgent


class PapersAgent(BaseAgent):
    """Collects AI research papers from arXiv, HuggingFace, PapersWithCode, etc."""

    def get_agent_name(self) -> str:
        return "papers"

    def collect(self) -> int:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] PapersAgent: starting collection...")
        total_new = 0
        for name, url in config.PAPER_FEEDS.items():
            papers = self._fetch_feed(name, url)
            if papers:
                added = self.add_items(papers)
                total_new += added
                print(f"  {name}: {len(papers)} fetched, {added} new")
            else:
                print(f"  {name}: 0 fetched")
            time.sleep(1)

        storage.cleanup_old_files("papers")
        print(f"PapersAgent: {total_new} new papers added.")
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

    @staticmethod
    def _detect_conference(text: str) -> str | None:
        text_lower = text.lower()
        for kw in config.CONFERENCE_KEYWORDS:
            if kw in text_lower:
                return kw.upper()
        return None

    @staticmethod
    def _clean_summary(raw: str) -> str:
        """Strip HTML tags and clean up arXiv-style summaries."""
        text = re.sub(r"<[^>]+>", "", raw)
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) > 500:
            text = text[:497] + "..."
        return text

    @staticmethod
    def _is_relevant(title: str, summary: str) -> bool:
        """Check if paper matches any PAPER_KEYWORDS."""
        text = (title + " " + summary).lower()
        return any(kw in text for kw in config.PAPER_KEYWORDS)

    def _fetch_feed(self, name: str, url: str) -> list[dict]:
        try:
            feed = feedparser.parse(url)
        except Exception as e:
            print(f"  Error fetching {name}: {e}")
            return []

        # 24h window — one day of papers per run
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        papers = []

        for entry in feed.entries:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            if not title or not link:
                continue

            # Get the best available summary
            raw_summary = entry.get("summary", entry.get("description", "")).strip()
            summary = self._clean_summary(raw_summary)
            if not summary:
                summary = f"Paper: {title}"

            authors = entry.get("author", "")
            published = self._parse_published(entry)

            # arXiv feeds often have no parsed date — accept those entries
            if published and published < cutoff:
                continue

            # Only keep papers matching our keywords
            if not self._is_relevant(title, summary):
                continue

            conference_tag = self._detect_conference(title + " " + summary)

            papers.append({
                "title": title,
                "link": link,
                "authors": authors,
                "summary": summary,
                "source": name,
                "published": published.isoformat() if published else datetime.now(timezone.utc).isoformat(),
                "conference_tag": conference_tag,
            })

        return papers[:30]  # Cap at 30 per feed
