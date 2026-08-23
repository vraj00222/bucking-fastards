import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))

from release_video import lyric_cues, lyric_lines


class ReleaseVideoTests(unittest.TestCase):
    def test_tags_are_not_captions(self):
        lyrics = "[verse]\nship it\n[chorus]\nrun the tests"
        self.assertEqual(lyric_lines(lyrics), ["ship it", "run the tests"])

    def test_cues_cover_all_lyric_lines_with_breathing_room(self):
        cues = lyric_cues("[verse]\nship it\n[chorus]\nrun the tests", 20)
        self.assertEqual([cue[0] for cue in cues], ["ship it", "run the tests"])
        self.assertGreaterEqual(cues[0][1], 2)
        self.assertLess(cues[-1][2], 20)


if __name__ == "__main__":
    unittest.main()
