#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import shutil
import sys

ROOT = Path(__file__).resolve().parent


def _find_default_source() -> Path | None:
    parent = ROOT.parent
    preferred = [
        parent / "Crypto_Certified_Switch_v6_0_0_WINDOWS",
        parent / "Crypto_Certified_Switch_v6_0_0_WINDOWS(1)",
    ]
    for candidate in preferred:
        if candidate.is_dir() and candidate.resolve() != ROOT.resolve():
            return candidate

    candidates = sorted(
        (
            p for p in parent.iterdir()
            if p.is_dir()
            and p.resolve() != ROOT.resolve()
            and p.name.lower().startswith("crypto_certified_switch")
        ),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def _latest_backup(project: Path) -> Path | None:
    backup_root = project / "backups"
    if not backup_root.is_dir():
        return None
    backups = sorted(
        (p for p in backup_root.iterdir() if p.is_dir()),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return backups[0] if backups else None


def _looks_like_backup(path: Path) -> bool:
    return any((path / name).exists() for name in (".env", "config.json", "state.db", "telegram_delivery.json"))


def _looks_like_project(path: Path) -> bool:
    return (path / "config.json").exists() and ((path / "data").is_dir() or (path / "backups").is_dir())


def _resolve_source(path: Path) -> tuple[Path, str]:
    path = path.expanduser().resolve()
    if not path.is_dir():
        raise FileNotFoundError(f"Pasta não encontrada: {path}")

    if _looks_like_project(path):
        # Prioriza os dados vivos da instalação antiga. Se não houver estado,
        # utiliza automaticamente o backup mais recente dessa instalação.
        live_has_data = any(
            candidate.exists()
            for candidate in (
                path / ".env",
                path / "config.json",
                path / "data" / "state.db",
                path / "data" / "telegram_delivery.json",
                path / "proposals",
            )
        )
        if live_has_data:
            return path, "instalação antiga"
        latest = _latest_backup(path)
        if latest:
            return latest, "backup mais recente"

    if _looks_like_backup(path):
        return path, "pasta de backup"

    raise ValueError(
        "A pasta escolhida não parece ser uma instalação nem um backup válido."
    )


def _create_safety_backup() -> Path:
    destination = ROOT / "backups" / (datetime.now().strftime("%Y%m%d_%H%M%S") + "_antes_migracao")
    destination.mkdir(parents=True, exist_ok=False)

    mapping = {
        ROOT / ".env": destination / ".env",
        ROOT / "config.json": destination / "config.json",
        ROOT / "data" / "state.db": destination / "state.db",
        ROOT / "data" / "telegram_delivery.json": destination / "telegram_delivery.json",
    }
    for source, target in mapping.items():
        if source.exists():
            shutil.copy2(source, target)

    proposals = ROOT / "proposals"
    if proposals.is_dir():
        shutil.copytree(proposals, destination / "proposals", dirs_exist_ok=True)
    return destination


def _validate_config(source: Path) -> None:
    config = source / "config.json"
    if config.exists():
        with config.open("r", encoding="utf-8-sig") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            raise ValueError("config.json antigo não contém um objeto JSON válido.")



def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _merge_env(old_path: Path, new_path: Path) -> None:
    current_lines = new_path.read_text(encoding="utf-8-sig").splitlines() if new_path.exists() else []
    current = _parse_env_file(new_path)
    old = _parse_env_file(old_path)
    # Dados antigos prevalecem, exceto a configuração RPC nova já preenchida.
    protected = {
        "HELIUS_API_KEY", "SOLANA_RPC_URL", "SOLANA_RPC_FALLBACK_URL",
        "SOLANA_RPC_ENABLE_HELIUS_BETA_FALLBACK", "SOLANA_RPC_TIMEOUT_SECONDS",
        "SOLANA_RPC_VALIDATE_ON_START",
    }
    merged = dict(current)
    for key, value in old.items():
        if key not in protected or not current.get(key, "").strip():
            merged[key] = value
    seen: set[str] = set()
    output: list[str] = []
    for line in current_lines:
        key = line.split("=", 1)[0].strip() if "=" in line else ""
        if key and key in merged:
            output.append(f"{key}={merged[key]}")
            seen.add(key)
        else:
            output.append(line)
    for key, value in merged.items():
        if key not in seen:
            output.append(f"{key}={value}")
    new_path.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")


def _merge_config(old_path: Path, new_path: Path) -> None:
    old = json.loads(old_path.read_text(encoding="utf-8-sig"))
    new = json.loads(new_path.read_text(encoding="utf-8-sig"))
    # Migra somente dados/configurações do usuário. Mantém versão, fixes e RPC novos.
    for key in ("wallets", "destination_wallets", "rules", "telegram", "backup"):
        if key in old:
            new[key] = old[key]
    # Preserva personalizações de Ethereum/BNB, mas não reintroduz RPC Solana antiga.
    for network in ("ethereum", "bnb"):
        if old.get("networks", {}).get(network):
            new.setdefault("networks", {})[network] = old["networks"][network]
    new_path.write_text(json.dumps(new, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _copy_data(source: Path) -> list[str]:
    _validate_config(source)
    copied: list[str] = []

    # Mescla configurações antigas sem remover recursos novos da v6.1.1.
    if (source / ".env").exists():
        _merge_env(source / ".env", ROOT / ".env")
        copied.append(".env (mesclado)")
    if (source / "config.json").exists():
        _merge_config(source / "config.json", ROOT / "config.json")
        copied.append("config.json (carteiras/destinos mesclados)")

    # Em um backup, state.db e telegram_delivery.json ficam na raiz da pasta.
    # Em uma instalação, ficam dentro de data/.
    candidates = [
        (source / "data" / "state.db", ROOT / "data" / "state.db", "data/state.db"),
        (source / "state.db", ROOT / "data" / "state.db", "data/state.db"),
        (
            source / "data" / "telegram_delivery.json",
            ROOT / "data" / "telegram_delivery.json",
            "data/telegram_delivery.json",
        ),
        (
            source / "telegram_delivery.json",
            ROOT / "data" / "telegram_delivery.json",
            "data/telegram_delivery.json",
        ),
    ]

    copied_targets: set[Path] = set()
    for old, new, label in candidates:
        normalized = new.resolve()
        if old.exists() and normalized not in copied_targets:
            new.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(old, new)
            copied.append(label)
            copied_targets.add(normalized)

    proposals = source / "proposals"
    if proposals.is_dir():
        target = ROOT / "proposals"
        target.mkdir(parents=True, exist_ok=True)
        shutil.copytree(proposals, target, dirs_exist_ok=True)
        copied.append("proposals/")

    return copied


def main() -> int:
    print("=" * 62)
    print(" CCS v6.1.1 — MIGRAR DADOS DA VERSÃO ANTERIOR")
    print("=" * 62)
    print()
    print("Feche o START_WINDOWS.bat antes de continuar.")
    print("Este processo não copia arquivos .py, .bat ou código antigo.")
    print()

    default = _find_default_source()
    if default:
        print(f"Pasta antiga detectada: {default}")
        answer = input("Usar esta pasta? [S/n]: ").strip().lower()
        source_input = default if answer in ("", "s", "sim", "y", "yes") else None
    else:
        source_input = None

    if source_input is None:
        raw = input("Cole o caminho da versão antiga ou da pasta de backup: ").strip().strip('"')
        if not raw:
            print("Migração cancelada: nenhum caminho informado.")
            return 1
        source_input = Path(raw)

    try:
        source, source_kind = _resolve_source(Path(source_input))
        print(f"Fonte selecionada ({source_kind}): {source}")
        print()
        print("Serão migrados, quando existentes:")
        print("  - .env")
        print("  - config.json")
        print("  - data\\state.db")
        print("  - data\\telegram_delivery.json")
        print("  - proposals\\")
        print()
        confirm = input("Continuar? [S/n]: ").strip().lower()
        if confirm not in ("", "s", "sim", "y", "yes"):
            print("Migração cancelada.")
            return 0

        safety = _create_safety_backup()
        copied = _copy_data(source)
        if not copied:
            print("Nenhum arquivo de dados compatível foi encontrado.")
            print(f"Backup de segurança preservado em: {safety}")
            return 1

        print()
        print("MIGRAÇÃO CONCLUÍDA COM SUCESSO.")
        print(f"Backup automático anterior à migração: {safety}")
        print("Itens migrados:")
        for item in copied:
            print(f"  OK  {item}")
        print()
        print("Agora execute START_WINDOWS.bat.")
        return 0
    except Exception as exc:
        print()
        print(f"ERRO NA MIGRAÇÃO: {exc}")
        print("Nenhum arquivo de código foi alterado.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
