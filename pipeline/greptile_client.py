"""Greptile v2 client: index a repo, poll, mine facts -> out/<slug>/facts.json"""
import argparse
import json
import os
import sys
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

BASE = "https://api.greptile.com/v2"
HEADERS = {
    "Authorization": f"Bearer {os.environ.get('GREPTILE_API_KEY', '')}",
    "X-GitHub-Token": os.environ.get("GITHUB_TOKEN", ""),
    "Content-Type": "application/json",
}


def gh_headers():
    tok = os.environ.get("GITHUB_TOKEN")
    return {"Authorization": f"Bearer {tok}"} if tok else {}

QUESTIONS = {
    "purpose": "In 2-3 sentences: what does this repo actually do, and who uses it?",
    "funny_names": "List the funniest, strangest, or most dramatic function/variable/file names, with paths.",
    "comments": "Find TODO, FIXME, HACK, XXX and any desperate or funny comments. Quote them exactly with file paths.",
    "commands": "What commands does a user actually run? Install, quickstart, the one killer command.",
    "notorious": "What's the most notorious/complex part of the codebase - biggest file, gnarliest module, legacy pain, weird dependency?",
}


def default_branch(repo):
    r = requests.get(
        f"https://api.github.com/repos/{repo}",
        headers=gh_headers(),
        timeout=15,
    )
    if r.ok:
        return r.json()
    return {"default_branch": "main", "stargazers_count": None, "language": None, "description": None}


def index(repo, branch):
    r = requests.post(
        f"{BASE}/repositories",
        headers=HEADERS,
        json={"remote": "github", "repository": repo, "branch": branch},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def poll(repo, branch, timeout_s=3600):
    rid = urllib.parse.quote(f"github:{branch}:{repo}", safe="")
    start = time.time()
    while time.time() - start < timeout_s:
        r = requests.get(f"{BASE}/repositories/{rid}", headers=HEADERS, timeout=30)
        status = r.json().get("status", "unknown") if r.ok else f"http {r.status_code}"
        print(f"  index status: {status} ({int(time.time() - start)}s)", flush=True)
        if status in ("completed", "COMPLETED", "ready"):
            return True
        if status in ("failed", "FAILED"):
            raise RuntimeError(f"indexing failed: {r.text}")
        time.sleep(15)
    raise TimeoutError("indexing timed out")


def query(repo, branch, question, genius=False):
    r = requests.post(
        f"{BASE}/query",
        headers=HEADERS,
        json={
            "messages": [{"content": question, "role": "user"}],
            "repositories": [{"remote": "github", "repository": repo, "branch": branch}],
            "stream": False,
            "genius": genius,
        },
        timeout=300,
    )
    r.raise_for_status()
    return r.json()


def mine(repo, branch=None, genius=False, skip_index=False):
    gh = default_branch(repo)
    branch = branch or gh.get("default_branch") or "main"
    if not skip_index:
        print(f"indexing {repo}@{branch} ...", flush=True)
        index(repo, branch)
        poll(repo, branch)
    print(f"mining {repo}@{branch} (genius={genius}) ...", flush=True)
    answers, sources = {}, []
    with ThreadPoolExecutor(max_workers=5) as ex:
        futs = {k: ex.submit(query, repo, branch, q, genius) for k, q in QUESTIONS.items()}
        for k, fut in futs.items():
            try:
                res = fut.result()
                answers[k] = res.get("message", "")
                sources += res.get("sources", []) or []
            except Exception as e:
                answers[k] = f"(query failed: {e})"
    return {
        "repo": repo,
        "branch": branch,
        "stars": gh.get("stargazers_count"),
        "language": gh.get("language"),
        "description": gh.get("description"),
        "answers": answers,
        "sources": sources,
    }


def slugify(repo):
    return repo.replace("/", "-").lower()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--branch")
    ap.add_argument("--genius", action="store_true")
    ap.add_argument("--skip-index", action="store_true")
    args = ap.parse_args()

    out = Path(__file__).parent.parent / "out" / slugify(args.repo)
    out.mkdir(parents=True, exist_ok=True)
    facts = mine(args.repo, args.branch, args.genius, args.skip_index)
    (out / "facts.json").write_text(json.dumps(facts, indent=2))
    print(f"wrote {out / 'facts.json'}")
    print(json.dumps(facts["answers"], indent=2)[:2000])
