from pathlib import Path

RUNTIME_DIRS = (
    "data",
    "logs",
    "backups",
    "proposals/pending",
    "proposals/submitted",
    "proposals/completed",
    "proposals/rejected",
    "proposals/failed",
)

def ensure_directories(root: Path) -> None:
    for relative in RUNTIME_DIRS:
        (root / relative).mkdir(parents=True, exist_ok=True)
