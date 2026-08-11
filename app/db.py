
from pathlib import Path
import sqlite3

def connect(root: Path):
    path = root / "data" / "state.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(path))
    db.execute("""
    CREATE TABLE IF NOT EXISTS assets(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      checked_at TEXT NOT NULL,
      wallet_id TEXT NOT NULL,
      network TEXT NOT NULL,
      address TEXT NOT NULL,
      asset_type TEXT NOT NULL,
      contract TEXT NOT NULL,
      symbol TEXT NOT NULL,
      name TEXT NOT NULL,
      amount REAL NOT NULL,
      raw_amount TEXT NOT NULL,
      decimals INTEGER NOT NULL,
      price_usd REAL NOT NULL,
      usd_value REAL NOT NULL,
      estimated_fee_usd REAL NOT NULL,
      net_value_usd REAL NOT NULL,
      recovery_score INTEGER NOT NULL
    )
    """)
    db.commit()
    return db
