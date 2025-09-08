# core/takeover_server.py
import asyncio
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn
from core.takeover import takeover

app = FastAPI()

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/takeover/status")
def status():
    return takeover.get_status()

HTML = """
<!doctype html><meta charset="utf-8">
<title>Rose Takeover</title>
<style>body{font-family:system-ui;margin:2rem}button{margin-right:.5rem;padding:.6rem 1rem}</style>
<h1>Rose — Takeover</h1>
<div id="step"></div>
<button onclick="act('approve')">Approve</button>
<button onclick="act('abort')">Abort</button>
<script>
async function poll(){
  const r = await fetch('/takeover/status'); const j = await r.json();
  document.getElementById('step').innerText = j.pending ? JSON.stringify(j.pending,null,2) : 'No pending step';
}
async function act(which){ await fetch('/takeover/'+which,{method:'POST'}); setTimeout(poll,300); }
setInterval(poll, 800); poll();
</script>
"""
@app.get("/", response_class=HTMLResponse)
def panel():
    return HTML

@app.post("/takeover/approve")
def approve():
    takeover.approve(); return {"ok": True}

@app.post("/takeover/abort")
def abort():
    takeover.abort(); return {"ok": True}

_server: uvicorn.Server | None = None

async def start_takeover_server(port: int = 8765):
    global _server
    if _server: return _server
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning", lifespan="off")
    _server = uvicorn.Server(config)
    asyncio.create_task(_server.serve())
    for _ in range(50):
        if _server.started: break
        await asyncio.sleep(0.05)
    return _server

async def stop_takeover_server():
    global _server
    if _server:
        _server.should_exit = True
        for _ in range(50):
            if _server.started is False: break
            await asyncio.sleep(0.05)
        _server = None