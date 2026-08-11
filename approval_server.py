
#!/usr/bin/env python3
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from ccs.core.paths import runtime_root
from urllib.parse import urlparse, quote
import html
import json
import os

from app.env import load
from app.proposals import find, move
from app.wallets import same
from app.runtime import ensure_directories
from app.http import HttpError
from app.solana_rpc import request_payload as solana_rpc_request

ROOT = runtime_root()
load(ROOT / ".env")

def config():
    return json.loads((ROOT / "config.json").read_text(encoding="utf-8"))

def json_response(handler, code, payload):
    data = json.dumps(payload).encode()
    handler.send_response(code)
    handler.send_header("Content-Type","application/json")
    handler.send_header("Content-Length",str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        return

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            return json_response(self, 200, {"ok": True})
        if parsed.path.startswith("/proposal/"):
            pid = parsed.path.rsplit("/",1)[-1]
            found = find(ROOT, pid)
            if not found:
                return json_response(self, 404, {"error":"Proposta não encontrada."})
            proposal, folder = found
            a, d = proposal["asset"], proposal["destination"]
            if same(a["network"], a["address"], d["address"]):
                return self.page("Destino inválido", "<h2>⛔ Origem e destino são iguais.</h2>")
            return self.proposal_page(proposal)
        return json_response(self, 404, {"error":"Não encontrado."})

    def page(self, title, body):
        content = f"<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>{html.escape(title)}</title></head><body>{body}</body></html>".encode()
        self.send_response(200)
        self.send_header("Content-Type","text/html; charset=utf-8")
        self.send_header("Content-Length",str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def proposal_page(self, proposal):
        a, d = proposal["asset"], proposal["destination"]
        pid, network = proposal["proposal_id"], a["network"]
        public_base = os.getenv("APPROVAL_BRIDGE_PUBLIC_URL", "").strip().rstrip("/")
        if public_base.startswith("https://"):
            current_url = f"{public_base}/proposal/{pid}"
        else:
            current_url = f"http://127.0.0.1:{os.getenv('APPROVAL_BRIDGE_PORT','8765')}/proposal/{pid}"
        phantom_browse = "https://phantom.app/ul/browse/" + quote(current_url, safe="") + "?ref=" + quote(current_url, safe="")
        wallet_name = "Phantom" if network in {"solana","ethereum"} else "Binance Web3"
        open_url = phantom_browse if network in {"solana","ethereum"} else current_url
        data = json.dumps(proposal, ensure_ascii=False)
        body = f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>CCS v7.0.0 SPL + ATA Automática</title>
<style>
:root{{--bg:#070910;--card:#171b2a;--line:#30364c;--text:#f5f7ff;--muted:#aeb6cc;--accent:#7d66ff;--green:#21c777;--red:#c84e65;--amber:#ffcb6b}}
*{{box-sizing:border-box}}body{{margin:0;background:linear-gradient(160deg,#06070c,#0d1120);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;padding:20px}}
.card{{max-width:680px;margin:auto;background:rgba(23,27,42,.98);border:1px solid var(--line);border-radius:26px;padding:24px;box-shadow:0 22px 70px rgba(0,0,0,.4)}}
h1{{font-size:28px;margin:0 0 12px}}.warn{{color:var(--amber);line-height:1.45}}.grid{{display:grid;gap:0;margin:22px 0}}
.row{{padding:15px 0;border-bottom:1px solid var(--line)}}.label{{color:var(--muted);font-size:14px}}.value{{font-size:19px;margin-top:4px;overflow-wrap:anywhere}}
button,a.btn{{display:block;width:100%;border:0;border-radius:16px;padding:17px;margin-top:12px;text-align:center;text-decoration:none;color:white;font-weight:800;font-size:17px}}
.open{{background:linear-gradient(135deg,var(--accent),#4da3ff)}}.confirm{{background:linear-gradient(135deg,var(--green),#0b9f65)}}.retry{{background:#293047}}.reject{{background:#512732}}.status{{margin-top:14px;padding:16px;border-radius:14px;background:#0c1020;line-height:1.45}}
.bad{{color:#ff8296}}.good{{color:#61e5a8}}small{{color:var(--muted)}}.review-check{{display:flex;gap:12px;align-items:flex-start;margin-top:16px;padding:15px;border:1px solid var(--line);border-radius:14px;background:#101526;line-height:1.4}}.review-check input{{width:22px;height:22px;flex:0 0 auto}}button:disabled{{opacity:.45;cursor:not-allowed}} 
</style></head>
<body><div class="card">
<h1>💠 Crypto Certified Switch v7.0.0</h1>
<p class="warn">Revise tudo. A carteira conectada deve ser a carteira de origem. A transação só é enviada após sua confirmação dentro da carteira.</p>
<div class="grid">
<div class="row"><div class="label">Ativo</div><div class="value">{html.escape(a['name'])} em {network}</div></div>
<div class="row"><div class="label">Quantidade</div><div class="value">{a['amount']:.8f} {html.escape(a['symbol'])}</div></div>
<div class="row"><div class="label">Origem</div><div class="value">{html.escape(a['address'])}</div></div>
<div class="row"><div class="label">Destino Trust Wallet</div><div class="value">{html.escape(d['address'])}</div></div>
<div class="row"><div class="label">Valor estimado</div><div class="value">US$ {a['usd_value']:.4f}</div></div>
</div>
<a class="btn open" id="openWallet" href="{html.escape(open_url)}">👛 Abrir {wallet_name}</a>
<label class="review-check">
<input type="checkbox" id="reviewed">
<span>Revisei a rede, a quantidade, a origem e o endereço de destino.</span>
</label>
<button class="confirm" id="confirm" disabled>🔐 Confirmar dentro da carteira</button>
<button class="retry" id="retry">🔄 Tentar abrir novamente</button>
<button class="reject" id="reject">🚫 Rejeitar proposta</button>
<div class="status" id="status">⏳ Aguardando abertura da carteira.</div>
<div class="status"><small>Link desta proposta: {html.escape(current_url)}</small></div>
<small>Se o navegador normal não detectar a carteira, use o botão “Abrir {wallet_name}”.</small>
</div>
<script src="https://cdn.jsdelivr.net/npm/@solana/web3.js@1.98.2/lib/index.iife.min.js"
        onerror="this.onerror=null;this.src='https://unpkg.com/@solana/web3.js@1.98.2/lib/index.iife.min.js';"></script>
<script>
const proposal={data};
const network=proposal.asset.network;
const status=document.getElementById('status');
const openWallet=document.getElementById('openWallet');
const reviewed=document.getElementById('reviewed');
const confirmButton=document.getElementById('confirm');
reviewed.addEventListener('change',()=>{{confirmButton.disabled=!reviewed.checked;}});
function setStatus(text,ok=false){{status.className='status '+(ok?'good':'');status.textContent=text}}
async function post(path,payload){{
 const r=await fetch(path,{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(payload)}});
 const j=await r.json();if(!r.ok)throw Error(j.error||'Falha');return j;
}}
async function evmConfirm(){{
 const provider=window.binancew3w?.ethereum||window.ethereum;
 if(!provider)throw Error('Carteira EVM não detectada. Abra pelo navegador DApp da carteira.');
 const accounts=await provider.request({{method:'eth_requestAccounts'}});
 const from=accounts[0];
 if(from.toLowerCase()!==proposal.asset.address.toLowerCase())throw Error('A carteira conectada não é a origem configurada.');
 let tx={{from,to:proposal.destination.address}};
 if(proposal.asset.asset_type==='NATIVE'){{
   tx.value='0x'+BigInt(proposal.asset.raw_amount).toString(16);
 }}else{{
   const to=proposal.destination.address.toLowerCase().replace(/^0x/,'').padStart(64,'0');
   const amount=BigInt(proposal.asset.raw_amount).toString(16).padStart(64,'0');
   tx.to=proposal.asset.contract;tx.data='0xa9059cbb'+to+amount;tx.value='0x0';
 }}
 const hash=await provider.request({{method:'eth_sendTransaction',params:[tx]}});
 await post('/api/submitted',{{proposal_id:proposal.proposal_id,hash}});
 setStatus('✅ Transação enviada. Hash: '+hash,true);
}}
const TOKEN_PROGRAM_ID='TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA';
const ASSOCIATED_TOKEN_PROGRAM_ID='ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL';

function u64LE(value){{
 let n=BigInt(value);const out=new Uint8Array(8);
 for(let i=0;i<8;i++){{out[i]=Number(n&255n);n>>=8n;}}
 return out;
}}

function associatedTokenAddress(web3,mint,owner){{
 const tokenProgram=new web3.PublicKey(TOKEN_PROGRAM_ID);
 const ataProgram=new web3.PublicKey(ASSOCIATED_TOKEN_PROGRAM_ID);
 return web3.PublicKey.findProgramAddressSync(
   [owner.toBuffer(),tokenProgram.toBuffer(),mint.toBuffer()],ataProgram
 )[0];
}}

function createAtaIdempotentInstruction(web3,payer,ata,owner,mint){{
 return new web3.TransactionInstruction({{
   programId:new web3.PublicKey(ASSOCIATED_TOKEN_PROGRAM_ID),
   keys:[
     {{pubkey:payer,isSigner:true,isWritable:true}},
     {{pubkey:ata,isSigner:false,isWritable:true}},
     {{pubkey:owner,isSigner:false,isWritable:false}},
     {{pubkey:mint,isSigner:false,isWritable:false}},
     {{pubkey:web3.SystemProgram.programId,isSigner:false,isWritable:false}},
     {{pubkey:new web3.PublicKey(TOKEN_PROGRAM_ID),isSigner:false,isWritable:false}}
   ],
   data:new Uint8Array([1])
 }});
}}

function transferCheckedInstruction(web3,source,mint,destination,owner,amount,decimals){{
 const amountBytes=u64LE(amount);const data=new Uint8Array(10);
 data[0]=12;data.set(amountBytes,1);data[9]=Number(decimals);
 return new web3.TransactionInstruction({{
   programId:new web3.PublicKey(TOKEN_PROGRAM_ID),
   keys:[
     {{pubkey:source,isSigner:false,isWritable:true}},
     {{pubkey:mint,isSigner:false,isWritable:false}},
     {{pubkey:destination,isSigner:false,isWritable:true}},
     {{pubkey:owner,isSigner:true,isWritable:false}}
   ],
   data
 }});
}}

async function findSourceTokenAccount(connection,web3,owner,mint,requiredAmount){{
 if(proposal.asset.token_account){{
   const candidate=new web3.PublicKey(proposal.asset.token_account);
   const parsed=await connection.getParsedAccountInfo(candidate,'confirmed');
   const info=parsed.value?.data?.parsed?.info;
   if(info?.owner===owner.toString() && info?.mint===mint.toString() && BigInt(info.tokenAmount.amount)>=requiredAmount)return candidate;
 }}
 const accounts=await connection.getParsedTokenAccountsByOwner(owner,{{mint}},'confirmed');
 for(const entry of accounts.value){{
   const info=entry.account.data.parsed.info;
   if(BigInt(info.tokenAmount.amount)>=requiredAmount)return entry.pubkey;
 }}
 throw Error('Conta SPL de origem não encontrada ou saldo insuficiente.');
}}

async function solanaConfirm(){{
 const provider=window.phantom?.solana;
 if(!provider?.isPhantom)throw Error('Phantom não detectada. Toque em “Abrir Phantom”.');
 const connected=await provider.connect();
 if(connected.publicKey.toString()!==proposal.asset.address)throw Error('A Phantom conectada não é a origem configurada.');
 const web3=window.solanaWeb3;
 if(!web3)throw Error('Biblioteca Solana não carregou. Feche e abra novamente pela Phantom.');
 const connection=new web3.Connection(window.location.origin+'/api/solana-rpc','confirmed');
 const tx=new web3.Transaction();
 if(proposal.asset.asset_type==='NATIVE'){{
   tx.add(web3.SystemProgram.transfer({{
     fromPubkey:connected.publicKey,
     toPubkey:new web3.PublicKey(proposal.destination.address),
     lamports:Number(proposal.asset.raw_amount)
   }}));
 }}else if(proposal.asset.asset_type==='SPL'){{
   const mint=new web3.PublicKey(proposal.asset.contract);
   const destinationOwner=new web3.PublicKey(proposal.destination.address);
   const rawAmount=BigInt(proposal.asset.raw_amount);
   const decimals=Number(proposal.asset.decimals);
   if(rawAmount<=0n)throw Error('Quantidade SPL inválida.');
   if(!Number.isInteger(decimals)||decimals<0||decimals>18)throw Error('Decimais SPL inválidos.');
   const mintInfo=await connection.getParsedAccountInfo(mint,'confirmed');
   const chainDecimals=Number(mintInfo.value?.data?.parsed?.info?.decimals);
   if(chainDecimals!==decimals)throw Error('Os decimais do token não conferem com a rede. Operação bloqueada.');
   const sourceAta=await findSourceTokenAccount(connection,web3,connected.publicKey,mint,rawAmount);
   const destinationAta=associatedTokenAddress(web3,mint,destinationOwner);
   const destinationExists=await connection.getAccountInfo(destinationAta,'confirmed');
   let ataRentLamports=0;
   if(!destinationExists){{
     ataRentLamports=await connection.getMinimumBalanceForRentExemption(165,'confirmed');
     tx.add(createAtaIdempotentInstruction(web3,connected.publicKey,destinationAta,destinationOwner,mint));
   }}
   tx.add(transferCheckedInstruction(web3,sourceAta,mint,destinationAta,connected.publicKey,rawAmount,decimals));
   tx.feePayer=connected.publicKey;
   const latest=await connection.getLatestBlockhash('confirmed');
   tx.recentBlockhash=latest.blockhash;
   const compiled=tx.compileMessage();
   const feeResult=await connection.getFeeForMessage(compiled,'confirmed');
   const feeLamports=Number(feeResult?.value||0);
   const solBalance=await connection.getBalance(connected.publicKey,'confirmed');
   const requiredLamports=ataRentLamports+feeLamports;
   const fmt=v=>(Number(v)/1_000_000_000).toFixed(9).replace(/0+$/,'').replace(/\.$/,'');
   const ataText=destinationExists
     ? 'A conta SPL do destino já existe.'
     : 'A conta SPL do destino será criada automaticamente nesta mesma transação.';
   setStatus('🔎 '+ataText+' Saldo: '+fmt(solBalance)+' SOL | necessário: '+fmt(requiredLamports)+' SOL (ATA '+fmt(ataRentLamports)+' + taxa '+fmt(feeLamports)+').');
   if(solBalance<requiredLamports){{
     const missing=requiredLamports-solBalance;
     throw Error('SOL insuficiente. Disponível: '+fmt(solBalance)+' SOL; necessário: '+fmt(requiredLamports)+' SOL; falta: '+fmt(missing)+' SOL. '+ataText);
   }}
 }}else{{
   throw Error('Tipo de ativo Solana não suportado.');
 }}
 if(!tx.feePayer)tx.feePayer=connected.publicKey;
 if(!tx.recentBlockhash){{
   const latest=await connection.getLatestBlockhash('confirmed');
   tx.recentBlockhash=latest.blockhash;
 }}
 if(proposal.asset.asset_type!=='SPL')setStatus('🔎 Transação montada. Revise cuidadosamente o ativo, a quantidade e o destino na Phantom.');
 const result=await provider.signAndSendTransaction(tx);
 const hash=result.signature;
 await post('/api/submitted',{{proposal_id:proposal.proposal_id,hash}});
 setStatus('✅ Transação enviada. Assinatura: '+hash,true);
}}
confirmButton.onclick=async()=>{{
 try{{setStatus('🔐 Abrindo confirmação da carteira...');network==='solana'?await solanaConfirm():await evmConfirm()}}
 catch(e){{setStatus('❌ '+e.message)}}
}};
document.getElementById('retry').onclick=()=>{{setStatus('🔄 Tentando abrir {wallet_name}...');window.location.href=openWallet.href}};
document.getElementById('reject').onclick=async()=>{{
 try{{await post('/api/reject',{{proposal_id:proposal.proposal_id}});setStatus('🚫 Proposta rejeitada.',true)}}
 catch(e){{setStatus('❌ '+e.message)}}
}};
setTimeout(()=>{{if(!window.phantom?.solana && !window.ethereum && !window.binancew3w?.ethereum)setStatus('⚠️ Carteira não detectada neste navegador. Use o botão “Abrir {wallet_name}”.')}},1800);
</script></body></html>"""
        return self.page("CCS v7.0.0", body)

    def do_POST(self):
        length=int(self.headers.get("Content-Length","0"))
        if length > 2_000_000:
            return json_response(self,413,{"error":"Requisição muito grande."})
        try:data=json.loads(self.rfile.read(length) or b"{}")
        except Exception:return json_response(self,400,{"error":"JSON inválido."})
        if self.path=="/api/solana-rpc":
            try:
                result=solana_rpc_request(data,config())
                return json_response(self,200,result)
            except HttpError as exc:
                return json_response(self,502,{
                    "jsonrpc":"2.0",
                    "id":data.get("id") if isinstance(data,dict) else None,
                    "error":{"code":-32098,"message":str(exc)}
                })
            except Exception as exc:
                return json_response(self,502,{
                    "jsonrpc":"2.0",
                    "id":data.get("id") if isinstance(data,dict) else None,
                    "error":{"code":-32099,"message":f"Falha no proxy RPC: {exc}"}
                })
        if self.path=="/api/submitted":
            proposal=move(ROOT,data["proposal_id"],"submitted","SUBMITTED",tx_hash=data["hash"])
            return json_response(self,200,{"ok":True,"proposal":proposal})
        if self.path=="/api/reject":
            proposal=move(ROOT,data["proposal_id"],"rejected","REJECTED")
            return json_response(self,200,{"ok":True,"proposal":proposal})
        return json_response(self,404,{"error":"Não encontrado."})

def serve():
    ensure_directories(ROOT)
    cfg=config()["approval_bridge"]
    host=os.getenv("APPROVAL_BRIDGE_HOST",cfg["host"])
    port=int(os.getenv("APPROVAL_BRIDGE_PORT",str(cfg["port"])))
    server=ThreadingHTTPServer((host,port),Handler)
    print(f"Approval Bridge v7.0.0 SPL + Helius RPC em http://{host}:{port}",flush=True)
    server.serve_forever()

if __name__=="__main__":
    serve()
