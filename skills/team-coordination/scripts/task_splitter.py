#!/usr/bin/env python3
"""Helper script to split tasks for team delegation."""

import json
import sys
from typing import Dict

TEAM_ROLES = [
    "researcher",
    "writer",
    "analyst",
    "editor",
    "coordinator",
]


def split_task(task: str, team_size: int = 3) -> Dict:
    """Split a task into subtasks for a team."""
    common_splits = {
        "research": [
            "Gather information from multiple sources",
            "Analyze and synthesize findings",
            "Prepare summary report",
        ],
        "write": [
            "Create first draft",
            "Add supporting content",
            "Review and edit",
        ],
        "analyze": [
            "Collect data",
            "Perform analysis",
            "Interpret results",
        ],
        "default": [
            f"Part 1 of {team_size}",
            f"Part 2 of {team_size}",
            f"Part 3 of {team_size}",
        ],
    }

    task_lower = task.lower()
    split = common_splits.get("default")

    for key in common_splits:
        if key in task_lower:
            split = common_splits[key]
            break

    return {
        "main_task": task,
        "subtasks": split[:team_size],
        "coordination": "Delegate subtasks to team members based on expertise",
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: task_splitter.py <task_description> [team_size]")
        sys.exit(1)

    task = sys.argv[1]
    team_size = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    result = split_task(task, team_size)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
