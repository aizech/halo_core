#!/usr/bin/env python3
"""Helper script to calculate optimal summary length."""

import json
import sys
from typing import Dict

LENGTH_GUIDELINES = {
    "short": {
        "source_length": "Under 500 words",
        "summary_length": "50-100 words",
        "ratio": "10-20%",
    },
    "medium": {
        "source_length": "500-2000 words",
        "summary_length": "100-300 words",
        "ratio": "5-15%",
    },
    "long": {
        "source_length": "Over 2000 words",
        "summary_length": "200-500 words",
        "ratio": "3-10%",
    },
    "executive": {
        "source_length": "Any",
        "summary_length": "1 paragraph",
        "ratio": "Variable",
    },
}


def calculate_summary_length(source_length: int, summary_type: str = "auto") -> Dict:
    """Calculate optimal summary length based on source."""
    if summary_type == "auto":
        if source_length < 500:
            summary_type = "short"
        elif source_length < 2000:
            summary_type = "medium"
        else:
            summary_type = "long"

    if summary_type not in LENGTH_GUIDELINES:
        return {"error": f"Unknown type: {summary_type}"}

    guideline = LENGTH_GUIDELINES[summary_type]

    return {
        "source_length": source_length,
        "summary_type": summary_type,
        "recommended_length": guideline["summary_length"],
        "ratio": guideline["ratio"],
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: length_calculator.py <source_length_words> [type]")
        print(f"Types: {', '.join(LENGTH_GUIDELINES.keys())}")
        sys.exit(1)

    source_length = int(sys.argv[1])
    summary_type = sys.argv[2] if len(sys.argv) > 2 else "auto"

    result = calculate_summary_length(source_length, summary_type)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
