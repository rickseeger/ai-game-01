"""Records persistence tests (DESIGN.md section 12)."""

import json
import os
import tempfile
import unittest

from emberlight import records


class LoadTest(unittest.TestCase):
    def test_missing_file_returns_defaults(self):
        rec = records.load_records(os.path.join(tempfile.mkdtemp(), "nope.json"))
        self.assertEqual(rec["best_depth"], 0)
        self.assertEqual(rec["runs"], 0)
        self.assertEqual(rec["daily"], {})

    def test_corrupt_file_returns_defaults(self):
        path = os.path.join(tempfile.mkdtemp(), "r.json")
        with open(path, "w") as fh:
            fh.write("{not valid json")
        rec = records.load_records(path)
        self.assertEqual(rec["runs"], 0)

    def test_save_then_load_roundtrip(self):
        path = os.path.join(tempfile.mkdtemp(), "r.json")
        rec = records._default_records()
        records.record_run(rec, seed_str="20260912", daily=True,
                           banked_score=1280, depth=4, root_lit=False,
                           survived=True)
        records.save_records(rec, path)
        loaded = records.load_records(path)
        self.assertEqual(loaded["total_banked"], 1280)
        self.assertEqual(loaded["daily"]["20260912"]["best_depth"], 4)


class RecordRunTest(unittest.TestCase):
    def test_bank_updates_totals(self):
        rec = records._default_records()
        records.record_run(rec, seed_str="1", daily=False, banked_score=900,
                           depth=3, root_lit=False, survived=True)
        self.assertEqual(rec["runs"], 1)
        self.assertEqual(rec["total_banked"], 900)
        self.assertEqual(rec["best_score"], 900)
        self.assertEqual(rec["best_depth"], 3)

    def test_death_does_not_bank(self):
        rec = records._default_records()
        records.record_run(rec, seed_str="1", daily=False, banked_score=0,
                           depth=5, root_lit=False, survived=False)
        self.assertEqual(rec["total_banked"], 0)
        self.assertEqual(rec["best_score"], 0)
        self.assertEqual(rec["best_depth"], 5)  # depth still recorded

    def test_root_lit_flag(self):
        rec = records._default_records()
        records.record_run(rec, seed_str="1", daily=False, banked_score=10,
                           depth=7, root_lit=True, survived=True)
        self.assertTrue(rec["root_lit"])

    def test_daily_table_only_on_daily_runs(self):
        rec = records._default_records()
        records.record_run(rec, seed_str="20260912", daily=True,
                           banked_score=100, depth=2, root_lit=False,
                           survived=True)
        records.record_run(rec, seed_str="999", daily=False,
                           banked_score=200, depth=3, root_lit=False,
                           survived=True)
        self.assertIn("20260912", rec["daily"])
        self.assertNotIn("999", rec["daily"])


if __name__ == "__main__":
    unittest.main()
