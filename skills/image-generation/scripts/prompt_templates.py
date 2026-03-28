#!/usr/bin/env python3
"""Helper script to generate image generation prompts."""

import json
import sys
from typing import Dict

STYLES = [
    "photorealistic",
    "illustration",
    "cartoon",
    "abstract",
    "watercolor",
    "oil painting",
    "3D render",
    "vector art",
    "anime/manga",
    "minimalist",
]

MEDIUMS = [
    "digital art",
    "photography",
    "oil on canvas",
    "watercolor",
    "charcoal sketch",
    "pencil drawing",
    "mixed media",
]

QUALITY_MODIFIERS = [
    "4k",
    "8k",
    "ultra detailed",
    "professional photography",
    "studio lighting",
    "high resolution",
    "masterpiece",
]


def generate_image_prompt(
    subject: str,
    style: str = "photorealistic",
    medium: str = None,
    quality: str = None,
    lighting: str = None,
    mood: str = None,
) -> Dict:
    """Generate an image generation prompt."""
    prompt_parts = [subject]

    if medium:
        prompt_parts.append(medium)
    prompt_parts.append(style)

    if lighting:
        prompt_parts.append(f"{lighting} lighting")
    if mood:
        prompt_parts.append(mood)
    if quality:
        prompt_parts.append(quality)

    return {
        "subject": subject,
        "style": style,
        "medium": medium,
        "lighting": lighting,
        "mood": mood,
        "quality": quality,
        "prompt": ", ".join(prompt_parts),
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: prompt_templates.py <subject> [options]")
        print(f"Styles: {', '.join(STYLES)}")
        print(f"Mediums: {', '.join(MEDIUMS[:5])}...")
        sys.exit(1)

    subject = sys.argv[1]
    style = (
        sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] in STYLES else "photorealistic"
    )
    medium = sys.argv[3] if len(sys.argv) > 3 else None
    quality = "high quality, detailed" if len(sys.argv) > 4 else None

    result = generate_image_prompt(subject, style, medium, quality)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
