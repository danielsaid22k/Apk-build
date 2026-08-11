import tempfile
import unittest
from pathlib import Path
from ccs.storage.json_cache import JsonCache

class CacheTests(unittest.TestCase):
    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            cache = JsonCache(Path(td) / "cache.json", 3600)
            cache.set("x", {"name": "Token"})
            value = cache.get("x")
            self.assertEqual(value["name"], "Token")
