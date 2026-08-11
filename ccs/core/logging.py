from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

_LOCK = Lock()

def log(root: Path, channel: str, level: str, message: str) -> None:
    path = root / "logs" / f"{channel}.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    line = f"{datetime.now(timezone.utc).isoformat()} [{level.upper()}] {message}"
    with _LOCK:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    print(f"{channel} [{level.upper()}]: {message}", flush=True)
