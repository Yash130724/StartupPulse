import html
import re
from datetime import datetime

from startup_pulse.core import config, storage

# Section definitions: (agent_name, display_title, color, max_items_in_email)
SECTIONS = [
    ("news",    "AI News",                "#0984E3", 25),
    ("papers",  "Research Papers",        "#6C5CE7", 20),
    ("grants",  "Grants & Schemes",       "#00B894", 15),
    ("funding", "Funding Opportunities",  "#E17055", 15),
    ("github",  "GitHub Trending",        "#2D3436", 25),
]


def _strip_html_tags(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


def _render_article(article: dict) -> str:
    title = html.escape(article.get("title", article.get("name", "")))
    link = html.escape(article.get("link", ""))
    source = html.escape(article.get("source", ""))
    summary = _strip_html_tags(article.get("summary", article.get("description", "")))
    summary = html.escape(summary)

    badges = f'<span style="display:inline-block;margin-top:6px;padding:2px 8px;background:#f0f0f5;border-radius:10px;font-size:11px;color:#666;font-weight:500;">{source}</span>'

    # Conference tag for papers
    conf = article.get("conference_tag")
    if conf:
        badges += f' <span style="display:inline-block;margin-top:6px;padding:2px 8px;background:#fff3e0;border-radius:10px;font-size:11px;color:#e65100;font-weight:500;">{html.escape(conf)}</span>'

    # Region badge for grants
    region = article.get("region")
    if region:
        badges += f' <span style="display:inline-block;margin-top:6px;padding:2px 8px;background:#e8f5e9;border-radius:10px;font-size:11px;color:#2e7d32;font-weight:500;">{html.escape(region)}</span>'

    # Type badge for funding
    ftype = article.get("type")
    if ftype:
        badges += f' <span style="display:inline-block;margin-top:6px;padding:2px 8px;background:#fce4ec;border-radius:10px;font-size:11px;color:#c62828;font-weight:500;">{html.escape(ftype)}</span>'

    # Tier 1 badge for news
    if article.get("source") in config.NEWS_TIER1:
        badges += ' <span style="display:inline-block;margin-top:6px;padding:2px 8px;background:#e3f2fd;border-radius:10px;font-size:11px;color:#1565c0;font-weight:500;">Tier 1</span>'

    summary_html = ""
    if summary:
        summary_html = f'<p style="margin:8px 0 0 0;color:#555;font-size:13px;line-height:1.55;">{summary}</p>'

    return f"""
            <div style="background:#ffffff;border-radius:6px;padding:16px 18px;margin-bottom:12px;border:1px solid #e8e8e8;">
                <a href="{link}" style="font-size:15px;color:#1a1a2e;text-decoration:none;font-weight:600;line-height:1.4;display:block;" target="_blank">{title}</a>
                {badges}
                {summary_html}
            </div>"""


def _render_github_repo(repo: dict) -> str:
    name = html.escape(repo.get("name", ""))
    link = html.escape(repo.get("link", ""))
    desc = html.escape(repo.get("description", ""))
    lang = repo.get("language", "")
    stars = repo.get("stars", 0)
    stars_today = repo.get("stars_today", 0)

    lang_badge = ""
    if lang:
        lang_badge = f'<span style="display:inline-block;margin-top:6px;padding:2px 8px;background:#f0f0f5;border-radius:10px;font-size:11px;color:#666;font-weight:500;">{html.escape(lang)}</span> '

    stars_text = f'<span style="display:inline-block;margin-top:6px;padding:2px 8px;background:#fff8e1;border-radius:10px;font-size:11px;color:#f57f17;font-weight:500;">&starf; {stars:,}</span>'
    today_text = ""
    if stars_today:
        today_text = f' <span style="display:inline-block;margin-top:6px;padding:2px 8px;background:#e8f5e9;border-radius:10px;font-size:11px;color:#2e7d32;font-weight:500;">+{stars_today:,} today</span>'

    desc_html = ""
    if desc:
        desc_html = f'<p style="margin:8px 0 0 0;color:#555;font-size:13px;line-height:1.55;">{desc}</p>'

    return f"""
            <div style="background:#ffffff;border-radius:6px;padding:16px 18px;margin-bottom:12px;border:1px solid #e8e8e8;">
                <a href="{link}" style="font-size:15px;color:#1a1a2e;text-decoration:none;font-weight:600;line-height:1.4;display:block;" target="_blank">{name}</a>
                {lang_badge}{stars_text}{today_text}
                {desc_html}
            </div>"""


def _render_section(title: str, color: str, items_html: str, count: int) -> str:
    return f"""
        <div style="margin-bottom:28px;padding-left:16px;border-left:4px solid {color};">
            <h2 style="margin:0 0 14px 0;font-size:17px;font-weight:700;color:{color};text-transform:uppercase;letter-spacing:0.5px;">{html.escape(title)}
                <span style="font-size:12px;font-weight:400;color:#999;margin-left:8px;">({count})</span>
            </h2>
{items_html}
        </div>"""


def _sort_news_tier1_first(items: list[dict]) -> list[dict]:
    """Sort news articles so Tier 1 sources appear before Tier 2."""
    tier1 = [a for a in items if a.get("source") in config.NEWS_TIER1]
    tier2 = [a for a in items if a.get("source") not in config.NEWS_TIER1]
    return tier1 + tier2


def format_digest(date: datetime | None = None) -> tuple[str, str]:
    """Format all agent data into a unified HTML email digest. Returns (subject, html_body)."""
    if date is None:
        date = datetime.now()

    date_str = date.strftime("%B %d, %Y")
    subject = f"Your Daily Briefing - {date_str}"

    sections_html = ""
    total_items = 0

    for agent_name, title, color, max_items in SECTIONS:
        items = storage.load_articles(agent_name, date)
        if not items:
            continue

        # Sort news by tier 1 first
        if agent_name == "news":
            items = _sort_news_tier1_first(items)

        total_collected = len(items)
        display_items = items[:max_items]
        total_items += total_collected

        if agent_name == "github":
            items_html = "\n".join(_render_github_repo(r) for r in display_items)
        else:
            items_html = "\n".join(_render_article(a) for a in display_items)

        # Show how many were truncated
        if total_collected > max_items:
            items_html += f'\n            <p style="text-align:center;color:#999;font-size:12px;margin-top:8px;">...and {total_collected - max_items} more not shown</p>'

        sections_html += _render_section(title, color, items_html, total_collected)

    if not sections_html:
        html_body = f"""<html><body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;margin:0;padding:0;background:#f4f4f8;">
        <div style="max-width:640px;margin:0 auto;padding:20px;">
            <div style="background:#1a1a2e;border-radius:10px 10px 0 0;padding:28px 30px;">
                <h1 style="margin:0;color:#ffffff;font-size:22px;font-weight:700;">Your Daily Briefing</h1>
                <p style="margin:6px 0 0 0;color:#a0a0c0;font-size:13px;">{date_str}</p>
            </div>
            <div style="background:#ffffff;padding:30px;border-radius:0 0 10px 10px;">
                <p style="color:#666;font-size:14px;">Nothing collected today. Run <code>python main.py --collect</code> first.</p>
            </div>
        </div>
        </body></html>"""
        return subject, html_body

    html_body = f"""<html>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;margin:0;padding:0;background:#f4f4f8;">
    <div style="max-width:640px;margin:0 auto;padding:20px;">

        <!-- Header -->
        <div style="background:#1a1a2e;border-radius:10px 10px 0 0;padding:28px 30px;">
            <h1 style="margin:0;color:#ffffff;font-size:22px;font-weight:700;">Your Daily Briefing</h1>
            <p style="margin:8px 0 0 0;color:#a0a0c0;font-size:13px;">{date_str} &nbsp;&middot;&nbsp; {total_items} items collected</p>
        </div>

        <!-- Content -->
        <div style="background:#fafafe;padding:28px 26px;border-radius:0 0 10px 10px;">
{sections_html}
            <!-- Footer -->
            <div style="border-top:1px solid #e8e8e8;margin-top:10px;padding-top:18px;text-align:center;">
                <p style="font-size:11px;color:#aaa;margin:0;">Curated by StartupPulse</p>
            </div>
        </div>

    </div>
</body>
</html>"""

    return subject, html_body
