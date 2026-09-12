"""Persistent local records (DESIGN.md section 12).

Load and save ``~/.emberlight/records.json`` (platform-appropriate path), and
the daily-seed table.  A path or ``EMBERLIGHT_HOME`` override keeps tests
hermetic.  Reads that fail (missing file, corrupt JSON) return defaults.
"""

import json
import os

from . import config


def _default_records():
    return {
        "best_depth": 0,
        "best_score": 0,
        "total_banked": 0,
        "runs": 0,
        "root_lit": False,
        "daily": {},
    }


def records_path():
    """Path to records.json, honouring an EMBERLIGHT_HOME override for tests."""
    base = os.environ.get("EMBERLIGHT_HOME") or os.path.expanduser("~")
    return os.path.join(base, ".emberlight", "records.json")


def load_records(path=None):
    """Return the records dict, defaulting gracefully on any read failure."""
    path = path or records_path()
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return _default_records()
    records = _default_records()
    if isinstance(data, dict):
        records.update({k: v for k, v in data.items() if k in records})
        if isinstance(data.get("daily"), dict):
            records["daily"] = dict(data["daily"])
    return records


def save_records(records, path=None):
    """Write the records dict to disk, creating parent directories."""
    path = path or records_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(records, fh, indent=2)
    return path


def record_run(records, *, seed_str, daily, banked_score, depth, root_lit,
               survived):
    """Fold one finished run into ``records`` in place (DESIGN.md section 12)."""
    records["runs"] = int(records.get("runs", 0)) + 1
    records["best_depth"] = max(int(records.get("best_depth", 0)), depth)
    if survived:
        records["total_banked"] = int(records.get("total_banked", 0)) + banked_score
        records["best_score"] = max(int(records.get("best_score", 0)), banked_score)
    if root_lit:
        records["root_lit"] = True
    if daily:
        day = records["daily"].setdefault(seed_str, {"best_score": 0, "best_depth": 0})
        day["best_depth"] = max(int(day.get("best_depth", 0)), depth)
        if survived:
            day["best_score"] = max(int(day.get("best_score", 0)), banked_score)
    return records
