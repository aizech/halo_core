#!/usr/bin/env python3
"""Helper script to analyze and categorize medical imaging findings."""

import json
import sys
from typing import Dict, List


def analyze_findings(findings: List[Dict]) -> Dict:
    """Analyze imaging findings and categorize by severity."""
    categories = {
        "critical": [],
        "significant": [],
        "minor": [],
        "normal": [],
    }

    critical_keywords = [
        "hemorrhage",
        "pneumothorax",
        "fracture",
        "stroke",
        "aneurysm",
        "embolism",
    ]

    for finding in findings:
        text = finding.get("finding", "").lower()
        if any(kw in text for kw in critical_keywords):
            categories["critical"].append(finding)
        elif "normal" in text or "unremarkable" in text:
            categories["normal"].append(finding)
        else:
            categories["significant"].append(finding)

    return {
        "summary": {
            "critical_count": len(categories["critical"]),
            "significant_count": len(categories["significant"]),
            "minor_count": len(categories["minor"]),
            "normal_count": len(categories["normal"]),
        },
        "categories": categories,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: analyze_findings.py <findings.json>")
        print("  Reads JSON array of findings from file, outputs analysis")
        sys.exit(1)

    with open(sys.argv[1], encoding="utf-8") as f:
        findings = json.load(f)

    result = analyze_findings(findings)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
