import json
import os
from datetime import datetime, timedelta

from startup_pulse.core import config


def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def agent_data_dir(agent_name: str) -> str:
    return os.path.join(config.DATA_DIR, agent_name)


def _filepath_for_date(agent_name: str, date: datetime) -> str:
    d = agent_data_dir(agent_name)
    return os.path.join(d, f"items_{date.strftime('%Y-%m-%d')}.json")


def load_articles(agent_name: str, date: datetime | None = None) -> list[dict]:
    if date is None:
        date = datetime.now()
    path = _filepath_for_date(agent_name, date)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_articles(agent_name: str, articles: list[dict], date: datetime | None = None):
    if date is None:
        date = datetime.now()
    d = agent_data_dir(agent_name)
    _ensure_dir(d)
    path = _filepath_for_date(agent_name, date)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False, default=str)


def add_articles(agent_name: str, new_articles: list[dict], date: datetime | None = None) -> int:
    """Add articles, deduplicating by URL. Returns count of newly added articles."""
    existing = load_articles(agent_name, date)
    existing_urls = {a["link"] for a in existing}
    added = 0
    for article in new_articles:
        if article["link"] not in existing_urls:
            existing.append(article)
            existing_urls.add(article["link"])
            added += 1
    if added > 0:
        save_articles(agent_name, existing, date)
    return added


def cleanup_old_files(agent_name: str | None = None):
    """Remove item files older than STORAGE_RETENTION_DAYS."""
    cutoff = datetime.now() - timedelta(days=config.STORAGE_RETENTION_DAYS)

    if agent_name:
        dirs = [agent_data_dir(agent_name)]
    else:
        _ensure_dir(config.DATA_DIR)
        dirs = []
        for entry in os.listdir(config.DATA_DIR):
            full = os.path.join(config.DATA_DIR, entry)
            if os.path.isdir(full):
                dirs.append(full)

    for d in dirs:
        if not os.path.isdir(d):
            continue
        for filename in os.listdir(d):
            if not filename.startswith("items_") or not filename.endswith(".json"):
                continue
            try:
                date_str = filename.replace("items_", "").replace(".json", "")
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
                if file_date < cutoff:
                    os.remove(os.path.join(d, filename))
                    print(f"  Cleaned up: {os.path.basename(d)}/{filename}")
            except ValueError:
                continue
