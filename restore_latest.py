from pathlib import Path
from app.backup import restore_latest
r=Path(__file__).resolve().parent
print(restore_latest(r).relative_to(r))
