import unittest
from unittest.mock import patch
from ccs.services.token_metadata import resolve_solana_token

class MetadataTests(unittest.TestCase):
    @patch("ccs.services.token_metadata._cache")
    @patch("ccs.services.token_metadata._dex_market")
    @patch("ccs.services.token_metadata._helius_metadata")
    def test_merge_sources(self, helius, dex, cache_factory):
        class MemoryCache:
            def get(self, key): return None
            def set(self, key, value): self.value = value
        cache_factory.return_value = MemoryCache()
        helius.return_value = {
            "name":"Example Token", "symbol":"EX", "image_url":"https://img.example/x.png",
            "metadata_source":"helius"
        }
        dex.return_value = {
            "price_usd":2.5, "liquidity_usd":1000, "market_cap_usd":50000,
            "market_source":"dexscreener"
        }
        result = resolve_solana_token("Mint123")
        self.assertEqual(result["name"], "Example Token")
        self.assertEqual(result["symbol"], "EX")
        self.assertEqual(result["price_usd"], 2.5)
        self.assertIn("helius", result["sources"])
        self.assertIn("dexscreener", result["sources"])
