#!/usr/bin/env python3
"""Helper script to format web search results."""

import json
import sys
from typing import Dict, List


def format_search_result(result: Dict) -> Dict:
    """Format a search result for consistency."""
    return {
        "title": result.get("title", "Untitled"),
        "url": result.get("url", ""),
        "description": result.get("description", "")[:300],
        "source": extract_domain(result.get("url", "")),
    }


def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    if not url:
        return ""
    try:
        from urllib.parse import urlparse

        return urlparse(url).netloc
    except Exception:
        return ""


def format_multiple_results(results: List[Dict]) -> Dict:
    """Format multiple search results."""
    formatted = [format_search_result(r) for r in results]

    return {
        "count": len(formatted),
        "results": formatted,
        "summary": f"Found {len(formatted)} sources from the web",
    }


def main():

    if len(sys.argv) < 2:
        print("Usage: search_formatter.py <json_results>")
        sys.exit(1)

    results = json.loads(sys.argv[1])
    formatted = format_multiple_results(results)
    print(json.dumps(formatted, indent=2))


if __name__ == "__main__":
    main()
