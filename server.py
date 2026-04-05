"""
LANStream — Multi-user LAN screen sharing (HTTPS)
Run:  pip install fastapi uvicorn websockets
Then: python server.py

WHY HTTPS? Browsers block screen/mic/camera APIs on plain http:// for
non-localhost addresses. A self-signed cert fixes this.
Your browser will show a "not secure" warning — just click
Advanced → Proceed. This is normal for self-signed certs on LAN.
"""

import json, uuid, socket, os, ssl, subprocess, sys

CERT_FILE = "cert.pem"
KEY_FILE  = "key.pem"

def generate_cert():
    print("📜  Generating self-signed certificate...")
    try:
        subprocess.run([
            "openssl", "req", "-x509", "-newkey", "rsa:2048",
            "-keyout", KEY_FILE, "-out", CERT_FILE,
            "-days", "365", "-nodes",
            "-subj", "/CN=lanstream"
        ], check=True, capture_output=True)
        print("✅  Certificate created.\n")
    except FileNotFoundError:
        print("❌  openssl not found.")
        print("    Install it:  sudo apt install openssl  (Linux)")
        print("              or brew install openssl      (Mac)")
        print("    Or on Windows: use Git Bash / WSL.\n")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print("❌  openssl failed:", e.stderr.decode())
        sys.exit(1)

if not (os.path.exists(CERT_FILE) and os.path.exists(KEY_FILE)):
    generate_cert()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
import uvicorn

app = FastAPI()

# ── State ──────────────────────────────────────────────────────────────────
streamers = {}   # stream_id  → { ws, name, viewers: set() }
viewers   = {}   # viewer_id  → { ws, watching: stream_id }
all_ws    = {}   # client_id  → ws

def stream_list():
    return [{"id": sid, "name": d["name"], "viewers": len(d["viewers"])}
            for sid, d in streamers.items()]

async def broadcast(msg: dict):
    data = json.dumps(msg)
    for ws in list(all_ws.values()):
        try: await ws.send_text(data)
        except: pass

async def push_stream_list():
    await broadcast({"type": "stream_list", "streams": stream_list()})

# ── Routes ─────────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return FileResponse(os.path.join(os.path.dirname(__file__), "index.html"))

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    cid = str(uuid.uuid4())
    all_ws[cid] = ws
    await ws.send_text(json.dumps({"type": "your_id", "id": cid}))
    await ws.send_text(json.dumps({"type": "stream_list", "streams": stream_list()}))

    try:
        while True:
            msg = json.loads(await ws.receive_text())
            t = msg.get("type")

            if t == "start_stream":
                streamers[cid] = {"ws": ws, "name": msg.get("name", "?"), "viewers": set()}
                await push_stream_list()

            elif t == "stop_stream":
                await _drop_streamer(cid)
                await push_stream_list()

            elif t == "join_stream":
                sid = msg.get("stream_id")
                if sid in streamers:
                    if cid in viewers:
                        old = viewers[cid]["watching"]
                        if old in streamers:
                            streamers[old]["viewers"].discard(cid)
                            await _send(streamers[old]["ws"], {"type": "viewer_left", "viewer_id": cid})
                    viewers[cid] = {"ws": ws, "watching": sid}
                    streamers[sid]["viewers"].add(cid)
                    await _send(streamers[sid]["ws"], {"type": "viewer_joined", "viewer_id": cid})
                    await push_stream_list()
                else:
                    await ws.send_text(json.dumps({"type": "error", "msg": "Stream gone"}))

            elif t == "leave_stream":
                await _drop_viewer(cid)
                await push_stream_list()

            elif t in ("offer", "answer", "ice"):
                msg["from"] = cid
                target_ws = all_ws.get(msg.get("target"))
                if target_ws:
                    await target_ws.send_text(json.dumps(msg))

    except WebSocketDisconnect:
        pass
    finally:
        await _drop_streamer(cid)
        await _drop_viewer(cid)
        all_ws.pop(cid, None)
        await push_stream_list()

async def _send(ws, msg):
    try: await ws.send_text(json.dumps(msg))
    except: pass

async def _drop_streamer(cid):
    if cid not in streamers: return
    for vid in list(streamers[cid]["viewers"]):
        vws = all_ws.get(vid)
        if vws:
            await _send(vws, {"type": "stream_ended", "stream_id": cid})
        viewers.pop(vid, None)
    streamers.pop(cid, None)

async def _drop_viewer(cid):
    if cid not in viewers: return
    sid = viewers[cid]["watching"]
    if sid in streamers:
        streamers[sid]["viewers"].discard(cid)
        await _send(streamers[sid]["ws"], {"type": "viewer_left", "viewer_id": cid})
    viewers.pop(cid, None)

if __name__ == "__main__":
    try:
        ip = socket.gethostbyname(socket.gethostname())
    except:
        ip = "127.0.0.1"

    print(f"🎮  LANStream running on HTTPS!")
    print(f"    Local  →  https://localhost:8000")
    print(f"    LAN    →  https://{ip}:8000")
    print(f"\n⚠️   Browser will warn 'Not Secure' — that's expected for self-signed certs.")
    print(f"    Click  Advanced → Proceed to {ip}  to continue.\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        ssl_certfile=CERT_FILE,
        ssl_keyfile=KEY_FILE,
    )