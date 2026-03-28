#!/usr/bin/env python3
"""Helper script to grade evidence quality using GRADE system."""

import json
import sys
from typing import Dict, List

GRADE_LEVELS = {
    "high": {
        "level": 4,
        "description": "Further research unlikely to change confidence in estimate",
    },
    "moderate": {
        "level": 3,
        "description": "Further research may change confidence",
    },
    "low": {
        "level": 2,
        "description": "Further research likely to change confidence",
    },
    "very_low": {
        "level": 1,
        "description": "Any estimate of effect is very uncertain",
    },
}


STUDY_TYPE_POINTS = {
    "systematic_review": 4,
    "rct": 3,
    "cohort": 2,
    "case_control": 1,
    "case_series": 0,
    "expert_opinion": -1,
}


def grade_evidence(
    study_type: str,
    factors_down: List[str] = None,
    factors_up: List[str] = None,
) -> Dict:
    """Grade evidence quality using GRADE system."""
    factors_down = factors_down or []
    factors_up = factors_up or []

    base_score = STUDY_TYPE_POINTS.get(study_type.lower().replace(" ", "_"), 0)

    for factor in factors_down:
        if factor in [
            "risk_of_bias",
            "inconsistency",
            "indirectness",
            "imprecision",
            "publication_bias",
        ]:
            base_score -= 1

    for factor in factors_up:
        if factor in ["large_effect", "dose_response", "all_plausible_bias"]:
            base_score += 1

    base_score = max(0, min(base_score, 4))

    if base_score >= 3:
        grade = "high"
    elif base_score == 2:
        grade = "moderate"
    elif base_score == 1:
        grade = "low"
    else:
        grade = "very_low"

    return {
        "study_type": study_type,
        "base_score": STUDY_TYPE_POINTS.get(study_type.lower().replace(" ", "_"), 0),
        "factors_down": factors_down,
        "factors_up": factors_up,
        "final_score": base_score,
        "grade": grade,
        "description": GRADE_LEVELS[grade]["description"],
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: grade_evidence.py <study_type> [factor1] [factor2] ...")
        print(
            "  Study types: systematic_review, rct, cohort, case_control, case_series, expert_opinion"
        )
        print(
            "  Factors down: risk_of_bias, inconsistency, indirectness, imprecision, publication_bias"
        )
        print("  Factors up: large_effect, dose_response, all_plausible_bias")
        sys.exit(1)

    study_type = sys.argv[1]
    factors = sys.argv[2:]

    factors_down = [
        f
        for f in factors
        if f
        in [
            "risk_of_bias",
            "inconsistency",
            "indirectness",
            "imprecision",
            "publication_bias",
        ]
    ]
    factors_up = [
        f
        for f in factors
        if f in ["large_effect", "dose_response", "all_plausible_bias"]
    ]

    result = grade_evidence(study_type, factors_down, factors_up)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
