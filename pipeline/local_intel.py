"""Fallback repo intel: shallow-clone + grep + Claude -> same facts.json shape as greptile_client."""
import json
import os
import subprocess
import tempfile
from pathlib import Path

import anthropic
import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

QUESTIONS = {
    "purpose": "In 2-3 sentences: what does this repo actually do, and who uses it?",
    "funny_names": "List the funniest, strangest, or most dramatic function/variable/file names, with paths.",
    "comments": "The funniest/most desperate TODO, FIXME, HACK comments. Quote them exactly with file paths.",
    "commands": "What commands does a user actually run? Install, quickstart, the one killer command.",
    "notorious": "The most notorious/complex part of the codebase - biggest file, gnarliest module, weird dependency.",
}


def sh(cmd, cwd=None):
    return subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True).stdout


def mine(repo, branch=None, **_):
    gh = requests.get(
        f"https://api.github.com/repos/{repo}",
        headers={"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}"},
        timeout=15,
    ).json()
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            ["git", "clone", "--depth", "1", f"https://github.com/{repo}", tmp],
            capture_output=True, check=True,
        )
        readme = ""
        for name in ("README.md", "README.rst", "README", "readme.md"):
            p = Path(tmp) / name
            if p.exists():
                readme = p.read_text(errors="ignore")[:5000]
                break
        todos = sh(r"grep -rn --include='*.*' -iE 'TODO|FIXME|HACK|XXX' . 2>/dev/null | grep -v node_modules | cut -c1-200 | head -80", cwd=tmp)
        files = sh("git ls-files | head -400", cwd=tmp)
        scripts = ""
        for f in ("package.json", "pyproject.toml", "Makefile", "justfile"):
            p = Path(tmp) / f
            if p.exists():
                scripts += f"\n--- {f} ---\n" + p.read_text(errors="ignore")[:2000]

    client = anthropic.Anthropic()
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2500,
        system="You analyze a codebase from raw material and answer questions with REAL, EXACT quotes, "
        "function names, file paths, and commands from the material. Never invent. Output ONLY a JSON "
        "object with keys: " + ", ".join(QUESTIONS) + ". Values are strings.",
        messages=[{
            "role": "user",
            "content": f"Repo: {repo} ({gh.get('description')})\n\nQuestions:\n{json.dumps(QUESTIONS, indent=1)}\n\n"
            f"README:\n{readme}\n\nTODO/FIXME/HACK grep:\n{todos}\n\nFile list:\n{files}\n\nScripts:\n{scripts}",
        }],
    )
    text = resp.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1].removeprefix("json").strip()
    answers = json.loads(text)

    sources = []
    for line in todos.splitlines()[:30]:
        parts = line.lstrip("./").split(":", 2)
        if len(parts) >= 2 and parts[1].isdigit():
            sources.append({"filepath": parts[0], "linestart": int(parts[1]),
                            "summary": parts[2][:120] if len(parts) > 2 else ""})
    return {
        "repo": repo,
        "branch": branch or gh.get("default_branch", "main"),
        "stars": gh.get("stargazers_count"),
        "language": gh.get("language"),
        "description": gh.get("description"),
        "answers": answers,
        "sources": sources,
        "intel_source": "local",
    }


if __name__ == "__main__":
    import sys
    print(json.dumps(mine(sys.argv[1]), indent=2)[:3000])
