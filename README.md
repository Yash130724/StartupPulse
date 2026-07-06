# StartupPulse

A small command-line tool that gathers AI news, research papers, government grants,
startup funding calls and trending GitHub repos once a day and emails you a single
digest. It's built around five independent collectors ("agents"), each responsible
for one type of source. Everything is stored as plain JSON on disk, so there's no
database to set up.

The grant and funding sources are India-focused (central schemes plus Telangana /
Andhra Pradesh), since that's what it was originally written for. Swap them out in
the config if you need something else.

## How it works

The flow is deliberately boring:

1. Each agent fetches its sources and writes new items to `data/<agent>/items_YYYY-MM-DD.json`.
2. New items are deduplicated by URL, so running collection twice in a day won't create duplicates.
3. The formatter reads today's JSON files and builds one HTML email.
4. The emailer sends it over Gmail SMTP.

Files older than 7 days are deleted automatically at the end of each collection run.

```
main.py  ──►  agents.collect()  ──►  data/<agent>/items_<date>.json
                                              │
                                              ▼
                       formatter.format_digest()  ──►  emailer.send_email()
```

The five agents:

| Agent   | How it collects        | Sources                                                                 |
|---------|------------------------|-------------------------------------------------------------------------|
| news    | RSS (`feedparser`)     | OpenAI, Google, Anthropic, DeepMind, NVIDIA, Microsoft, MIT TR, The Verge, TechCrunch, VentureBeat |
| papers  | RSS (`feedparser`)     | 7 arXiv categories, Hugging Face Papers, Papers With Code               |
| grants  | HTML scraping (`bs4`)  | Startup India, MEITY, DST, MSME, BIRAC, T-Hub, WE-Hub, and others       |
| funding | HTML scraping (`bs4`)  | Y Combinator, Antler, 100X.VC, Techstars, IAN, Better Capital, T-Hub    |
| github  | HTML scraping (`bs4`)  | github.com/trending (daily and weekly)                                  |

All five inherit from `BaseAgent` and implement a single `collect()` method. They run
one after another, and an exception in one is caught and printed rather than aborting
the whole run — a dead feed won't stop the rest of the digest from going out.

## Setup

Requires Python 3.10+ (the code uses `X | None` type hints).

```bash
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env` with a Gmail address and an **app password** (not your normal
password). To get one: turn on 2-step verification for the account, then generate a
password under Google Account → Security → App passwords → Mail.

```
GMAIL_ADDRESS=you@gmail.com
GMAIL_APP_PASSWORD=xxxxxxxxxxxxxxxx
RECIPIENT_EMAIL=where-to-send@example.com
```

## Usage

```bash
python main.py --collect            # run every agent, save to disk, don't email
python main.py --collect-agent news # run one agent (news|papers|grants|funding|github)
python main.py --send               # build and send the digest from today's saved data
python main.py --daily              # collect everything, then send — the normal path
```

`--daily` is what you'd schedule. If you only want to preview what a digest looks
like without re-scraping, run `--collect` once and then `--send` as many times as you
like.

## Scheduling

There's no built-in scheduler; use whatever your OS provides.

cron (Linux / macOS), every morning at 8:

```
0 8 * * * cd /path/to/StartupPulse && /usr/bin/python3 main.py --daily
```

Windows Task Scheduler: create a basic daily task that starts `python`, with
`main.py --daily` as the argument and the project folder as the working directory.

## Layout

```
main.py                     CLI entry point / argument parsing
startup_pulse/
  core/
    config.py               all feeds, scrape targets, keywords, email + storage settings
    storage.py              JSON read/write, URL dedup, 7-day cleanup
  agents/
    base.py                 BaseAgent abstract class
    news.py, papers.py, grants.py, funding.py, github.py
    __init__.py             the ALL_AGENTS registry
  delivery/
    formatter.py            builds the HTML email
    emailer.py              Gmail SMTP send
data/                       generated JSON, one folder per agent (git-ignored)
```

## Notes on each agent

- **news** — keeps entries published in the last 24 hours. Feeds are split into two
  tiers; tier-1 (company blogs, MIT TR, The Verge) sort to the top of the section and
  get a badge.
- **papers** — 24-hour window, capped at 30 per feed. arXiv entries without a parsed
  date are kept. An item is only included if its title or abstract matches one of the
  keyword lists in `config.py`, and titles/abstracts are scanned for conference names
  (NeurIPS, ICML, CVPR, …) to add a tag.
- **grants** / **funding** — these scrape link text off each portal and keep only
  links whose text contains a "strong" keyword (scheme, grant, apply, accelerator, …)
  while dropping obvious navigation noise (login, privacy, social links, …). Grants
  also drop anything that looks expired. Capped at 10 and 8 items per source.
- **github** — parses `article.Box-row` blocks from the trending page for name,
  description, language, total stars and stars gained in the period.

Because grants and funding rely on scraping arbitrary government/VC sites, they're the
most fragile part — a site redesign will quietly return zero items for that source
until the selectors are adjusted. The keyword filters live at the top of each agent
file so they're easy to tune.

## Changing sources

Almost everything you'd want to edit is in `startup_pulse/core/config.py`: the RSS
feed dictionaries, the grant/funding URL lists, the keyword lists, and
`STORAGE_RETENTION_DAYS`. Adding a new feed is a one-line change; adding a whole new
agent means subclassing `BaseAgent` and registering it in `agents/__init__.py`.
