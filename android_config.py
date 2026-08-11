from __future__ import annotations
from pathlib import Path
import json, os, shutil

DEFAULT_ENV = {
    'ENABLE_TELEGRAM':'true','TELEGRAM_BOT_TOKEN':'','TELEGRAM_CHAT_ID':'',
    'TELEGRAM_HEARTBEAT_SECONDS':'60','TELEGRAM_RETRY_ATTEMPTS':'3','TELEGRAM_RETRY_DELAY_SECONDS':'3',
    'TELEGRAM_COLLECTION_RECEIPT':'true','POLL_INTERVAL_SECONDS':'100',
    'APPROVAL_BRIDGE_HOST':'127.0.0.1','APPROVAL_BRIDGE_PORT':'8765','APPROVAL_BRIDGE_BASE_URL':'http://127.0.0.1:8765',
    'APPROVAL_BRIDGE_PUBLIC_URL':'','AUTO_BACKUP_ENABLED':'true','AUTO_BACKUP_INTERVAL_SECONDS':'3600','AUTO_BACKUP_KEEP':'20',
    'HELIUS_API_KEY':'','SOLANA_RPC_URL':'','SOLANA_RPC_FALLBACK_URL':'','SOLANA_RPC_ENABLE_HELIUS_BETA_FALLBACK':'false',
    'SOLANA_RPC_TIMEOUT_SECONDS':'20','SOLANA_RPC_VALIDATE_ON_START':'true',
    'ETHEREUM_RPC_URL':'https://ethereum-rpc.publicnode.com','BNB_RPC_URL':'https://bsc-rpc.publicnode.com',
    'TOKEN_METADATA_CACHE_TTL_SECONDS':'21600','SOLANA_RPC_FAILURE_COOLDOWN_SECONDS':'30'
}

def parse_env(path: Path) -> dict[str,str]:
    out={}
    if path.exists():
        for raw in path.read_text(encoding='utf-8-sig').splitlines():
            line=raw.strip()
            if not line or line.startswith('#') or '=' not in line: continue
            k,v=line.split('=',1); out[k.strip()]=v.strip().strip('"').strip("'")
    return out

def write_env(path: Path, values: dict[str,str]) -> None:
    merged={**DEFAULT_ENV, **values}
    lines=['# Crypto Certified Switch Android — configurações privadas']
    for k,v in merged.items(): lines.append(f'{k}={str(v).strip()}')
    tmp=path.with_suffix('.tmp'); tmp.write_text('\n'.join(lines)+'\n',encoding='utf-8'); tmp.replace(path)
    try: os.chmod(path,0o600)
    except OSError: pass

def ensure_runtime(package_root: Path, runtime_root: Path) -> tuple[Path,Path]:
    runtime_root.mkdir(parents=True,exist_ok=True)
    for d in ('data','logs','backups','proposals/pending','proposals/submitted','proposals/completed','proposals/rejected','proposals/failed'):
        (runtime_root/d).mkdir(parents=True,exist_ok=True)
    cfg=runtime_root/'config.json'; env=runtime_root/'.env'
    if not cfg.exists(): shutil.copy2(package_root/'config.json',cfg)
    if not env.exists(): write_env(env,DEFAULT_ENV)
    os.environ['CCS_RUNTIME_ROOT']=str(runtime_root)
    return cfg,env

def load_settings(cfg_path: Path, env_path: Path):
    return json.loads(cfg_path.read_text(encoding='utf-8')), {**DEFAULT_ENV, **parse_env(env_path)}

def save_settings(cfg_path: Path, env_path: Path, config: dict, env: dict):
    tmp=cfg_path.with_suffix('.tmp'); tmp.write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); tmp.replace(cfg_path)
    write_env(env_path,env)
