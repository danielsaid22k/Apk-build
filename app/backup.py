
from datetime import datetime
from pathlib import Path
import shutil

def create(root: Path, keep: int = 20) -> Path:
    dest = root / "backups" / datetime.now().strftime("%Y%m%d_%H%M%S")
    dest.mkdir(parents=True, exist_ok=True)
    for relative in ("config.json", ".env", "data/state.db", "data/telegram_delivery.json"):
        source = root / relative
        if source.exists():
            shutil.copy2(source, dest / source.name)
    if (root / "proposals").exists():
        shutil.copytree(root / "proposals", dest / "proposals", dirs_exist_ok=True)
    backups = sorted(
        [p for p in (root / "backups").iterdir() if p.is_dir()],
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    for old in backups[max(1, keep):]:
        shutil.rmtree(old, ignore_errors=True)
    return dest

def restore_latest(root: Path) -> Path:
    backups = sorted(
        [p for p in (root / "backups").iterdir() if p.is_dir()],
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    if not backups:
        raise FileNotFoundError("Nenhum backup disponível.")
    latest = backups[0]
    mapping = {
        "config.json": root / "config.json",
        ".env": root / ".env",
        "state.db": root / "data" / "state.db",
        "telegram_delivery.json": root / "data" / "telegram_delivery.json"
    }
    for name, target in mapping.items():
        source = latest / name
        if source.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    if (latest / "proposals").exists():
        shutil.copytree(latest / "proposals", root / "proposals", dirs_exist_ok=True)
    return latest
