#!/usr/bin/env python3
"""Helper script for data analysis calculations."""

import json
import sys
from typing import Dict, List
from statistics import mean, median, stdev, variance


def calculate_descriptive(values: List[float]) -> Dict:
    """Calculate descriptive statistics for a list of values."""
    if not values:
        return {"error": "No values provided"}

    return {
        "count": len(values),
        "sum": sum(values),
        "mean": mean(values),
        "median": median(values),
        "min": min(values),
        "max": max(values),
        "range": max(values) - min(values),
        "variance": variance(values) if len(values) > 1 else 0,
        "stdev": stdev(values) if len(values) > 1 else 0,
    }


def calculate_percentile(values: List[float], percentile: float) -> float:
    """Calculate a specific percentile."""
    if not values:
        return 0.0
    sorted_values = sorted(values)
    index = (len(sorted_values) - 1) * (percentile / 100)
    floor = int(index)
    ceil = floor + 1
    if ceil >= len(sorted_values):
        return sorted_values[floor]
    return sorted_values[floor] * (ceil - index) + sorted_values[ceil] * (index - floor)


def calculate_growth_rate(old_value: float, new_value: float) -> Dict:
    """Calculate growth rate between two values."""
    if old_value == 0:
        return {"error": "Cannot calculate growth rate from zero"}

    change = new_value - old_value
    percent_change = (change / old_value) * 100

    return {
        "old_value": old_value,
        "new_value": new_value,
        "absolute_change": change,
        "percent_change": percent_change,
        "growth": "positive" if change > 0 else "negative" if change < 0 else "none",
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: calc_helper.py <command> [args...]")
        print("Commands:")
        print("  descriptive <v1> <v2> ... - Calculate descriptive stats")
        print("  growth <old> <new> - Calculate growth rate")
        print("  percentile <p> <v1> <v2> ... - Calculate percentile")
        sys.exit(1)

    command = sys.argv[1]

    if command == "descriptive":
        values = [float(x) for x in sys.argv[2:]]
        result = calculate_descriptive(values)
    elif command == "growth":
        old = float(sys.argv[2])
        new = float(sys.argv[3])
        result = calculate_growth_rate(old, new)
    else:
        result = {"error": f"Unknown command: {command}"}

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
