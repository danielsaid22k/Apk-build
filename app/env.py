from __future__ import annotations

from pathlib import Path
import os


def parse(path: Path) -> dict[str, str]:
    """Lê um arquivo .env simples sem depender de python-dotenv."""
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        if key:
            values[key] = value
    return values


def load(path: Path, *, override: bool = True) -> dict[str, str]:
    """
    Carrega o .env.

    Por padrão, o arquivo substitui variáveis antigas exportadas no Termux.
    Isso evita que um TELEGRAM_CHAT_ID antigo prevaleça sobre o valor salvo.
    """
    values = parse(path)
    for key, value in values.items():
        if override or key not in os.environ:
            os.environ[key] = value
    return values


def load_env(path, *, override: bool = True) -> dict[str, str]:
    """Compatibilidade com versões anteriores."""
    return load(Path(path), override=override)


def as_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "sim", "on"}
