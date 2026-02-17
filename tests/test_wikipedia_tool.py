from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

from agno.agent import Agent
from agno.tools.wikipedia import WikipediaTools


def main() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    load_dotenv(env_path)
    agent = Agent(tools=[WikipediaTools()])
    result = agent.run("Search wikipedia for 'Nagold'")
    print(result)


if __name__ == "__main__":
    main()
