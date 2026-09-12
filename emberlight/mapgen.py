"""Seeded procedural floor generation (DESIGN.md sections 9 and 9.1).

Node 3 implements the recursive-backtracker maze, loop carving, connectivity
guarantee, beacon placement, and entity scatter, all driven by a single
seeded PRNG so a seed reproduces an identical run.
"""
