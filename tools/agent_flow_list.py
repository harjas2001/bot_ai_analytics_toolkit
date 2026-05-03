"""
tools/agent_flow_list.py
─────────────────────────────────────────────────────────────────────────────
Iterates through an exported conversational AI agent configuration and
prints a complete list of all pages grouped by flow.

Useful for auditing flow structure, mapping terminal/last pages, and
identifying orphaned or unreachable pages before a production deployment.

Built for Dialogflow CX export structure but adaptable to any platform
that organises flows → pages as directories of JSON files.

Configuration (via .env):
  AGENT_FLOWS_PATH — path to the flows folder in your agent export
─────────────────────────────────────────────────────────────────────────────
"""

import os
from dotenv import load_dotenv

load_dotenv()

AGENT_FLOWS_PATH = os.getenv("AGENT_FLOWS_PATH", "agent_export/flows")


def get_flow_pages(flows_path: str) -> dict:
    """
    Walk the flows directory and return a mapping of flow → [page names].

    Expected structure:
      <flows_path>/
        <flow-name>/
          pages/
            <page-name>.json
    """
    flow_pages = {}

    if not os.path.isdir(flows_path):
        print(f"Flows directory not found: {flows_path}")
        return flow_pages

    for flow_name in os.listdir(flows_path):
        flow_path  = os.path.join(flows_path, flow_name)
        pages_path = os.path.join(flow_path, "pages")

        if os.path.isdir(flow_path) and os.path.isdir(pages_path):
            json_files = [f for f in os.listdir(pages_path) if f.endswith(".json")]
            page_names = [os.path.splitext(f)[0] for f in json_files]
            if page_names:
                flow_pages[flow_name] = sorted(page_names)

    return flow_pages


def print_flow_pages(flow_pages: dict) -> None:
    """Print all pages grouped by flow in a readable format."""
    if not flow_pages:
        print("No flows or pages found.")
        return

    total_pages = sum(len(p) for p in flow_pages.values())
    print(f"\n{len(flow_pages)} flows — {total_pages} pages total\n")

    for flow, pages in sorted(flow_pages.items()):
        print(f"{flow}")
        print("-" * len(flow))
        for page in pages:
            print(f"  {page}")
        print()


if __name__ == "__main__":
    flow_pages = get_flow_pages(AGENT_FLOWS_PATH)
    print_flow_pages(flow_pages)
