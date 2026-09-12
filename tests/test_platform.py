"""Windows / cross-platform hardening tests (node 4 Windows port).

Covers the automatic ASCII-glyph fallback for terminals that cannot render
the unicode block-shade / heart glyphs (legacy Windows code pages) and the
EMBERLIGHT_ASCII override.
"""

import unittest

from emberlight import input as input_mod


class _FakeStream:
    def __init__(self, encoding):
        self.encoding = encoding


class _FakeSys:
    """Stand-in for the ``sys`` module exposing only what prefer_ascii reads."""

    def __init__(self, encoding):
        self.stdout = _FakeStream(encoding)


class PreferAsciiTests(unittest.TestCase):
    def setUp(self):
        self._saved_sys = input_mod.sys
        self._had_ascii = "EMBERLIGHT_ASCII" in input_mod.os.environ
        self._ascii_val = input_mod.os.environ.get("EMBERLIGHT_ASCII")

    def tearDown(self):
        input_mod.sys = self._saved_sys
        if self._had_ascii:
            input_mod.os.environ["EMBERLIGHT_ASCII"] = self._ascii_val
        else:
            input_mod.os.environ.pop("EMBERLIGHT_ASCII", None)

    def _with_encoding(self, encoding):
        input_mod.sys = _FakeSys(encoding)

    def test_utf8_keeps_unicode(self):
        self._with_encoding("utf-8")
        self.assertFalse(input_mod.prefer_ascii())

    def test_cp437_keeps_unicode(self):
        # cp437 includes the block elements and card suits.
        self._with_encoding("cp437")
        self.assertFalse(input_mod.prefer_ascii())

    def test_cp1252_forces_ascii(self):
        self._with_encoding("cp1252")
        self.assertTrue(input_mod.prefer_ascii())

    def test_latin1_forces_ascii(self):
        self._with_encoding("latin-1")
        self.assertTrue(input_mod.prefer_ascii())

    def test_env_override_forces_ascii(self):
        self._with_encoding("utf-8")
        input_mod.os.environ["EMBERLIGHT_ASCII"] = "1"
        self.assertTrue(input_mod.prefer_ascii())


if __name__ == "__main__":
    unittest.main()
