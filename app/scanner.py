"""Compatibilidade v6 -> v7. O scanner real está em ccs.core.scanner."""
from ccs.core.scanner import native_price, save_assets, scan_all, scan_wallet, score
__all__ = ["native_price", "save_assets", "scan_all", "scan_wallet", "score"]
