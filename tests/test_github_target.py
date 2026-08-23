import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))

from github_target import parse_target
from lyricist import build_lyric_evidence
from validate_source_queue import validate


class GitHubTargetTests(unittest.TestCase):
    def test_parses_repository_reference(self):
        self.assertEqual(
            parse_target("https://github.com/openai/codex"),
            {
                "kind": "repository",
                "repo": "openai/codex",
                "label": "openai/codex",
                "slug": "openai-codex",
            },
        )

    def test_parses_pull_request_reference(self):
        target = parse_target("openai/codex/pull/123")
        self.assertEqual(target["kind"], "pull-request")
        self.assertEqual(target["repo"], "openai/codex")
        self.assertEqual(target["number"], 123)
        self.assertEqual(target["slug"], "openai-codex-pr-123")

    def test_rejects_non_github_target(self):
        with self.assertRaises(ValueError):
            parse_target("https://example.com/openai/codex/pull/123")

    def test_parses_public_profile_reference(self):
        self.assertEqual(
            parse_target("https://github.com/garrytan"),
            {"kind": "profile", "login": "garrytan", "label": "@garrytan"},
        )

    def test_lyric_evidence_keeps_only_source_locators(self):
        evidence = build_lyric_evidence(
            {
                "repo": "openai/codex",
                "answers": {"architecture": "CLI flows through cli/src/main.rs."},
                "sources": [{"filepath": "cli/src/main.rs", "content": "discard this payload"}],
                "github_context": {"active_issues": [{"number": 1, "title": "An issue"}]},
            }
        )
        source = evidence["greptile_analysis"]["source_locators"][0]
        self.assertEqual(source, {"filepath": "cli/src/main.rs"})
        self.assertNotIn("content", source)


class SourceQueueTests(unittest.TestCase):
    def test_imported_queue_is_safe_and_valid(self):
        queue = json.loads((ROOT / "data/source-review-queue.json").read_text())
        self.assertEqual(validate(queue), [])
        self.assertTrue(all(record["trustLevel"] == "untrusted" for record in queue["records"]))
        self.assertTrue(all(record["reviewerDecision"] == "pending" for record in queue["records"]))


if __name__ == "__main__":
    unittest.main()
