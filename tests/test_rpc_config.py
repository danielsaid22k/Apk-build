import os
import unittest
from unittest.mock import patch
from ccs.services.solana_rpc import configured_endpoints, redact_url

class RpcConfigTests(unittest.TestCase):
    def test_redaction(self):
        safe = redact_url("https://mainnet.helius-rpc.com/?api-key=SECRET")
        self.assertNotIn("SECRET", safe)
        self.assertIn("%2A%2A%2A", safe)

    def test_order_prefers_explicit_then_helius(self):
        config = {"networks":{"solana":{"rpc_url":"https://legacy.example"}}}
        with patch.dict(os.environ, {
            "SOLANA_RPC_URL":"https://primary.example",
            "HELIUS_API_KEY":"abc",
            "SOLANA_RPC_FALLBACK_URL":"https://fallback.example",
            "SOLANA_RPC_ENABLE_HELIUS_BETA_FALLBACK":"false",
        }, clear=False):
            endpoints = configured_endpoints(config)
            self.assertEqual(endpoints[0], "https://primary.example")
            self.assertIn("mainnet.helius-rpc.com", endpoints[1])
            self.assertIn("https://fallback.example", endpoints)
