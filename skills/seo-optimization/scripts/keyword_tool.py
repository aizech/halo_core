#!/usr/bin/env python3
"""Helper script for SEO keyword analysis."""

import json
import sys
from typing import Dict, List

KEYWORD_CATEGORIES = {
    "informational": ["what", "how", "why", "guide", "tutorial"],
    "transactional": ["buy", "price", "discount", "deal", "shop"],
    "navigational": ["brand name", "product name", "login"],
    "commercial": ["review", "best", "vs", "compare", "alternative"],
}


def analyze_keyword(keyword: str) -> Dict:
    """Analyze a keyword for SEO purposes."""
    keyword_lower = keyword.lower()
    category = None
    for cat, terms in KEYWORD_CATEGORIES.items():
        if any(term in keyword_lower for term in terms):
            category = cat
            break

    word_count = len(keyword.split())

    difficulty = "low" if word_count >= 4 else "medium" if word_count >= 2 else "high"

    return {
        "keyword": keyword,
        "word_count": word_count,
        "category": category or "generic",
        "difficulty": difficulty,
        "intent": "long-tail" if word_count >= 3 else "short-tail",
    }


def generate_keyword_variations(keyword: str, count: int = 10) -> List[str]:
    """Generate keyword variations."""
    keyword_lower = keyword.lower()
    variations = [keyword]

    prefixes = ["best", "top", "how to", "what is", "why", "guide to"]
    suffixes = ["for beginners", "review", "2024", "tips", "examples"]

    for p in prefixes[:count]:
        if p not in keyword_lower:
            variations.append(f"{p} {keyword}")

    for s in suffixes[:count]:
        if s not in keyword_lower:
            variations.append(f"{keyword} {s}")

    return variations[:count]


def main():
    if len(sys.argv) < 2:
        print("Usage: keyword_tool.py <keyword>")
        sys.exit(1)

    keyword = sys.argv[1]
    result = analyze_keyword(keyword)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
