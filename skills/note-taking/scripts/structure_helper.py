#!/usr/bin/env python3
"""Helper script to structure notes."""

import json
import sys
from typing import Dict

STRUCTURES = {
    "cornell": {
        "name": "Cornell Method",
        "columns": ["Cue/Questions", "Notes", "Summary"],
        "description": "Two-column format for lecture/study notes",
    },
    "outline": {
        "name": "Outline",
        "format": "Hierarchical bullets",
        "description": "Nested bullet points for organized notes",
    },
    "mindmap": {
        "name": "Mind Map",
        "format": "Radial structure",
        "description": "Central topic with branches",
    },
    "box": {
        "name": "Box Method",
        "format": "Categorized boxes",
        "description": "Group related concepts in boxes",
    },
    "chart": {
        "name": "Comparison Chart",
        "format": "Table/matrix",
        "description": "Compare items across criteria",
    },
}


def structure_notes(topic: str, structure_type: str = "outline") -> Dict:
    """Generate a note structure template."""
    if structure_type not in STRUCTURES:
        return {"error": f"Unknown structure: {structure_type}"}

    structure = STRUCTURES[structure_type]

    return {
        "topic": topic,
        "structure": structure_type,
        "name": structure["name"],
        "description": structure["description"],
        "format": structure.get("format", ""),
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: structure_helper.py <topic> [structure_type]")
        print(f"Types: {', '.join(STRUCTURES.keys())}")
        sys.exit(1)

    topic = sys.argv[1]
    structure_type = sys.argv[2] if len(sys.argv) > 2 else "outline"

    result = structure_notes(topic, structure_type)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
