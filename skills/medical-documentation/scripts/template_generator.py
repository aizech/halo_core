#!/usr/bin/env python3
"""Helper script to generate medical documentation templates."""

import json
import sys
from typing import Dict

TEMPLATES = {
    "soap": {
        "name": "SOAP Note",
        "sections": ["Subjective", "Objective", "Assessment", "Plan"],
        "description": "Standard clinical note format",
    },
    "progress": {
        "name": "Progress Note",
        "sections": ["Date/Time", "Patient ID", "Provider", "Note Type", "Content"],
        "description": "Daily progress update",
    },
    "discharge": {
        "name": "Discharge Summary",
        "sections": [
            "Admission Date",
            "Discharge Date",
            "Chief Complaint",
            "Hospital Course",
            "Discharge Diagnosis",
            "Medications",
            "Follow-up",
            "Discharge Instructions",
        ],
        "description": "End of stay summary",
    },
    "referral": {
        "name": "Referral Letter",
        "sections": [
            "Referring Provider",
            "Date",
            "Patient Info",
            "Reason",
            "Clinical Notes",
            "Urgency",
        ],
        "description": "Specialist referral",
    },
    "case_report": {
        "name": "Case Report (CARE)",
        "sections": ["Introduction", "Case Presentation", "Discussion", "Conclusion"],
        "description": "Medical case publication format",
    },
}


def generate_template(template_type: str, custom_fields: Dict = None) -> Dict:
    """Generate a medical documentation template."""
    if template_type not in TEMPLATES:
        return {"error": f"Unknown template: {template_type}"}

    template = TEMPLATES[template_type].copy()
    template["custom_fields"] = custom_fields or {}

    return template


def main():
    if len(sys.argv) < 2:
        print("Usage: template_generator.py <template_type>")
        print(f"Available: {', '.join(TEMPLATES.keys())}")
        sys.exit(1)

    template_type = sys.argv[1]
    result = generate_template(template_type)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
