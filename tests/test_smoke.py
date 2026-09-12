"""Trivial smoke tests for the node 2 skeleton.

Run with:

    python -m unittest discover -s tests -v

No third-party test framework is used: unittest ships in the standard library,
so the harness runs unchanged on Linux and Windows (and CI).
"""

import re
import unittest

import emberlight
from emberlight import ai, config, engine, entities, input, main, mapgen
from emberlight import records, render, ui


class VersionTest(unittest.TestCase):
    def test_version_is_set(self):
        self.assertTrue(re.fullmatch(r"\d+\.\d+\.\d+", emberlight.__version__))


class ConfigTest(unittest.TestCase):
    def test_shade_ramp_has_five_steps(self):
        self.assertEqual(len(config.SHADE_RAMP), 5)

    def test_seven_rings(self):
        self.assertEqual(config.RING_COUNT, 7)
        self.assertEqual(len(config.RING_SIDES), 7)
        self.assertEqual(len(config.ENTITY_BUDGET), 7)

    def test_fuel_cap_matches_spec(self):
        self.assertEqual(config.MAX_FUEL, 100)

    def test_light_radius_shrinks_with_fuel(self):
        self.assertEqual(config.light_radius_for_fuel(100), 6)
        self.assertEqual(config.light_radius_for_fuel(50), 3)
        self.assertEqual(config.light_radius_for_fuel(0), config.LIGHT_RADIUS_MIN)


class RenderTest(unittest.TestCase):
    def test_near_wall_is_full_block(self):
        self.assertEqual(render.shade_for(1.0), "\u2588")

    def test_far_wall_is_space(self):
        self.assertEqual(render.shade_for(100.0), " ")

    def test_ascii_fallback_uses_plain_glyph(self):
        self.assertEqual(render.shade_for(1.0, ascii_fallback=True), "#")

    def test_title_is_nonempty(self):
        self.assertTrue(render.TITLE)
        self.assertTrue(any("EMBERLIGHT" in line for line in render.TITLE))

    def test_demo_frame_renders_lines(self):
        lines = render.demo_frame()
        self.assertTrue(lines)
        # every line is plain text (no control characters)
        self.assertTrue(all("\x1b" not in line for line in lines))


class ImportTest(unittest.TestCase):
    def test_all_engine_modules_import(self):
        for module in (config, engine, entities, ai, render, input, records, ui, mapgen, main):
            self.assertTrue(hasattr(module, "__name__"))


if __name__ == "__main__":
    unittest.main()
