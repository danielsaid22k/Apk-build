
from datetime import datetime, timezone
from pathlib import Path
import json
import secrets

from .wallets import same

FOLDERS = ("pending", "submitted", "completed", "rejected", "failed")

def _dir(root: Path, folder: str) -> Path:
    path = root / "proposals" / folder
    path.mkdir(parents=True, exist_ok=True)
    return path

def _same_pending_transfer(root: Path, asset: dict, destination: dict) -> bool:
    """Prevent the scanner from creating the same unsigned transfer repeatedly."""
    for proposal in pending(root):
        current = proposal.get("asset", {})
        target = proposal.get("destination", {})
        if (
            current.get("network") == asset.get("network")
            and current.get("address") == asset.get("address")
            and current.get("asset_type") == asset.get("asset_type")
            and current.get("contract", "") == asset.get("contract", "")
            and str(current.get("raw_amount", "")) == str(asset.get("raw_amount", ""))
            and target.get("address") == destination.get("address")
        ):
            return True
    return False


def create(root: Path, config: dict, asset: dict) -> dict | None:
    network = asset["network"]
    destination = config.get("destination_wallets", {}).get(network, {})
    if not destination.get("enabled"):
        return None
    if same(network, asset["address"], destination.get("address", "")):
        return None
    if asset.get("net_value_usd", 0) <= 0:
        return None
    if asset.get("recovery_score", 0) < config.get("rules", {}).get("min_recovery_score", 40):
        return None
    if _same_pending_transfer(root, asset, destination):
        return None
    proposal = {
        "proposal_id": secrets.token_hex(8),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "PENDING_WALLET_CONFIRMATION",
        "asset": asset,
        "destination": destination
    }
    save(root, proposal, "pending")
    return proposal

def save(root: Path, proposal: dict, folder: str) -> Path:
    path = _dir(root, folder) / f"{proposal['proposal_id']}.json"
    path.write_text(json.dumps(proposal, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path

def find(root: Path, proposal_id: str):
    for folder in FOLDERS:
        path = _dir(root, folder) / f"{proposal_id}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8")), folder
    return None

def move(root: Path, proposal_id: str, folder: str, status: str, **extra):
    found = find(root, proposal_id)
    if not found:
        raise FileNotFoundError("Proposta não encontrada.")
    proposal, old = found
    (_dir(root, old) / f"{proposal_id}.json").unlink(missing_ok=True)
    proposal["status"] = status
    proposal.update(extra)
    save(root, proposal, folder)
    return proposal

def pending(root: Path):
    result = []
    for path in _dir(root, "pending").glob("*.json"):
        result.append(json.loads(path.read_text(encoding="utf-8")))
    return sorted(result, key=lambda x: x.get("created_at", ""), reverse=True)
