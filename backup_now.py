from pathlib import Path
from app.backup import create
r=Path(__file__).resolve().parent
print(create(r).relative_to(r))
