#!/usr/bin/env python3
"""Helper script to generate content creation prompts."""

import json
import sys
from typing import Dict

CONTENT_TYPES = {
    "blog_post": {
        "length": "500-2000 words",
        "structure": ["Hook", "Introduction", "Main Points", "Conclusion", "CTA"],
        "tone": "Professional yet engaging",
    },
    "article": {
        "length": "1000-3000 words",
        "structure": [
            "Title",
            "Abstract",
            "Introduction",
            "Methods",
            "Results",
            "Discussion",
            "Conclusion",
        ],
        "tone": "Academic but accessible",
    },
    "social_post": {
        "length": "50-280 characters",
        "structure": ["Hook", "Message", "Hashtags"],
        "tone": "Casual, engaging",
    },
    "product_copy": {
        "length": "50-200 words",
        "structure": ["Headline", "Benefits", "Features", "CTA"],
        "tone": "Persuasive, benefit-driven",
    },
    "newsletter": {
        "length": "300-800 words",
        "structure": ["Greeting", "Main Story", "Secondary Items", "Closing"],
        "tone": "Personal, valuable",
    },
}


def generate_prompt(content_type: str, topic: str, audience: str = "general") -> Dict:
    """Generate a content creation prompt."""
    if content_type not in CONTENT_TYPES:
        return {"error": f"Unknown content type: {content_type}"}

    template = CONTENT_TYPES[content_type]

    prompt = f"""Create a {template['length']} {content_type.replace('_', ' ')} about {topic}.
Target audience: {audience}
Tone: {template['tone']}

Structure:
{chr(10).join(f"- {s}" for s in template['structure'])}

Requirements:
- Engaging hook/opening
- Clear value proposition
- Actionable conclusion
- Match the specified tone"""

    return {
        "content_type": content_type,
        "topic": topic,
        "audience": audience,
        "prompt": prompt,
        "structure": template["structure"],
    }


def main():
    if len(sys.argv) < 3:
        print("Usage: prompt_templates.py <content_type> <topic> [audience]")
        print(f"Available types: {', '.join(CONTENT_TYPES.keys())}")
        sys.exit(1)

    content_type = sys.argv[1]
    topic = sys.argv[2]
    audience = sys.argv[3] if len(sys.argv) > 3 else "general"

    result = generate_prompt(content_type, topic, audience)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
