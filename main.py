import argparse
import sys

from dotenv import load_dotenv

load_dotenv()

from startup_pulse.delivery import emailer, formatter
from startup_pulse.agents import ALL_AGENTS, COLLECTIBLE_AGENTS


def collect_all() -> int:
    """Run collection for all collectible agents."""
    total = 0
    for name, agent_cls in COLLECTIBLE_AGENTS.items():
        try:
            agent = agent_cls()
            total += agent.collect()
        except Exception as e:
            print(f"Error in {name} agent: {e}")
    return total


def collect_agent(name: str) -> int:
    """Run collection for a single agent by name."""
    agent_cls = ALL_AGENTS.get(name)
    if not agent_cls:
        print(f"Unknown agent: {name}. Available: {', '.join(ALL_AGENTS.keys())}", file=sys.stderr)
        sys.exit(1)
    agent = agent_cls()
    return agent.collect()


def main():
    parser = argparse.ArgumentParser(description="StartupPulse - Collect and digest")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--collect", action="store_true", help="Collect all agents")
    group.add_argument("--collect-agent", metavar="NAME", help="Collect a specific agent (news, papers, grants, funding, github)")
    group.add_argument("--send", action="store_true", help="Send the unified digest email now")
    group.add_argument("--daily", action="store_true", help="Collect all agents then send digest")

    args = parser.parse_args()

    if args.collect:
        count = collect_all()
        print(f"Done. {count} new items collected across all agents.")

    elif args.collect_agent:
        count = collect_agent(args.collect_agent)
        print(f"Done. {count} new items collected by {args.collect_agent} agent.")

    elif args.send:
        subject, html_body = formatter.format_digest()
        if emailer.send_email(subject, html_body):
            print("Digest sent successfully.")
        else:
            print("Failed to send digest.", file=sys.stderr)
            sys.exit(1)

    elif args.daily:
        count = collect_all()
        print(f"Collected {count} new items across all agents.")
        subject, html_body = formatter.format_digest()
        if emailer.send_email(subject, html_body):
            print("Digest sent successfully.")
        else:
            print("Failed to send digest.", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
