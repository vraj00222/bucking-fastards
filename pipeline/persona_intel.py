"""Public internet-persona facts for a repo owner / PR author, via Claude web search.

Boundary: public professional/persona material only (their own public posts,
talks, launches, press coverage, community reaction). Never private life,
family, contacts, or protected traits. Output is untrusted reference data.
"""
import json
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

SYSTEM = """You research the PUBLIC internet persona of a software figure so a satire
songwriter can reference them accurately. Use web search.

Hard rules:
- Public professional/persona material ONLY: their own public posts, talks,
  launches, open-source work, press coverage, memes and community reaction.
- NEVER collect private life, family, home, health, contacts, or protected traits.
- Every fact must be short (one line), verifiable, and sourced from what you found.
- If the person has no notable public internet presence, say so; do not pad.

Output ONLY a JSON object:
{"is_public_figure": bool, "facts": ["<one-line fact>", ...],  // max 15
 "joke_angles": ["<one-line work-targeted angle>", ...],       // max 6
 "provenance": "web search, public sources only, untrusted reference data"}"""


def gather(login, name=None, context=None, cache_path=None):
    """Return persona dict for a GitHub login; cache to cache_path if given."""
    cache = Path(cache_path) if cache_path else None
    if cache and cache.exists():
        return json.loads(cache.read_text())
    who = f"GitHub user '{login}'" + (f" (public name: {name})" if name else "")
    if context:
        ctx = " ".join(str(context).split())[:300]
        who += f" — context: {ctx}"
    client = anthropic.Anthropic()
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=3000,  # search summaries + JSON; 1500 truncated the JSON
        system=SYSTEM,
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}],
        messages=[{"role": "user", "content": f"Research the public internet persona of {who}."}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text").strip()
    if "```" in text:
        text = text.split("```")[1].removeprefix("json").strip()
    start = text.find("{")
    persona = json.loads(text[start:]) if start >= 0 else {"is_public_figure": False, "facts": []}
    persona["login"] = login
    if cache:
        cache.write_text(json.dumps(persona, indent=2))
    return persona


if __name__ == "__main__":
    import sys
    print(json.dumps(gather(sys.argv[1], name=sys.argv[2] if len(sys.argv) > 2 else None), indent=2))
