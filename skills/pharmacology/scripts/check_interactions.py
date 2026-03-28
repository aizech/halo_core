#!/usr/bin/env python3
"""Helper script to check drug interactions by severity."""

import json
import sys
from typing import Dict, List

INTERACTION_SEVERITY = {
    "contraindicated": {"level": 4, "label": "Contraindicated - Do not use"},
    "major": {"level": 3, "label": "Major - Significant clinical impact"},
    "moderate": {"level": 2, "label": "Moderate - May require monitoring"},
    "minor": {"level": 1, "label": "Minor - Minimal clinical significance"},
}


def check_interactions(drugs: List[str]) -> Dict:
    """Check for known drug interactions."""
    interactions_found = []

    common_interactions = {
        ("warfarin", "aspirin"): {
            "severity": "major",
            "effect": "Increased bleeding risk",
        },
        ("warfarin", "ibuprofen"): {
            "severity": "major",
            "effect": "Increased bleeding risk",
        },
        ("lisinopril", "potassium"): {"severity": "major", "effect": "Hyperkalemia"},
        ("metformin", "contrast"): {
            "severity": "moderate",
            "effect": "Lactic acidosis risk",
        },
        ("ssri", "maoi"): {
            "severity": "contraindicated",
            "effect": "Serotonin syndrome",
        },
        ("simvastatin", "erythromycin"): {
            "severity": "major",
            "effect": "Rhabdomyolysis risk",
        },
    }

    drugs_lower = [d.lower() for d in drugs]

    for i, drug1 in enumerate(drugs_lower):
        for drug2 in drugs_lower[i + 1 :]:
            pair = tuple(sorted([drug1, drug2]))
            if pair in common_interactions:
                interactions_found.append(
                    {
                        "drugs": pair,
                        "severity": common_interactions[pair]["severity"],
                        "effect": common_interactions[pair]["effect"],
                    }
                )

    sorted_interactions = sorted(
        interactions_found,
        key=lambda x: INTERACTION_SEVERITY.get(x["severity"], {}).get("level", 0),
        reverse=True,
    )

    return {
        "drugs_checked": drugs,
        "interaction_count": len(sorted_interactions),
        "interactions": sorted_interactions,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: check_interactions.py <drug1> <drug2> ...")
        print("  Checks for known drug interactions")
        sys.exit(1)

    drugs = sys.argv[1:]
    result = check_interactions(drugs)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
