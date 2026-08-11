from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import time

class JsonCache:
    def __init__(self, path: Path, ttl_seconds: int = 21600):
        self.path = path
        self.ttl_seconds = max(60, int(ttl_seconds))

    def _read(self) -> dict:
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else {}
        except Exception:
            return {}

    def _write(self, value: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp.replace(self.path)

    def get(self, key: str):
        data = self._read()
        item = data.get(key)
        if not isinstance(item, dict):
            return None
        created = float(item.get("_cached_at_epoch", 0) or 0)
        if not created or time.time() - created > self.ttl_seconds:
            return None
        result = dict(item)
        result.pop("_cached_at_epoch", None)
        return result

    def set(self, key: str, value: dict) -> None:
        data = self._read()
        item = dict(value)
        item["_cached_at_epoch"] = time.time()
        item["_cached_at"] = datetime.now(timezone.utc).isoformat()
        data[key] = item
        self._write(data)

    def purge_expired(self) -> int:
        data = self._read()
        now = time.time()
        kept = {}
        removed = 0
        for key, item in data.items():
            if not isinstance(item, dict):
                removed += 1
                continue
            created = float(item.get("_cached_at_epoch", 0) or 0)
            if created and now - created <= self.ttl_seconds:
                kept[key] = item
            else:
                removed += 1
        if removed:
            self._write(kept)
        return removed
