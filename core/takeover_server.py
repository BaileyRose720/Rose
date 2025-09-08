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
<title>Rose — Takeover</title>
<script>
async function fetchJSON(u, opts){const r=await fetch(u,opts);return r.json();}
async function poll(){
  const s = await fetchJSON('/takeover/status');
  document.getElementById('pending').textContent = s.pending ? JSON.stringify(s.pending, null, 2) : '—';
  document.getElementById('waiting').textContent = s.waiting ? 'Waiting for your decision' : 'Idle';
}
async function act(which){ await fetch('/takeover/'+which,{method:'POST'}); setTimeout(poll,300); }
setInterval(poll, 800); window.onload=poll;
</script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/tailwindcss@3.4.12/dist/tailwind.min.css">
<body class="bg-gray-50 text-gray-900">
  <div class="max-w-3xl mx-auto py-10 px-6">
    <h1 class="text-3xl font-semibold mb-6">🌹 Rose — Takeover</h1>
    <div class="mb-4 p-4 bg-white shadow rounded">
      <div class="flex items-center justify-between">
        <div>
          <div class="text-sm text-gray-500">Status</div>
          <div id="waiting" class="text-lg font-medium">—</div>
        </div>
        <div class="space-x-2">
          <button onclick="act('approve')" class="px-4 py-2 rounded bg-emerald-600 text-white hover:bg-emerald-700">Approve</button>
          <button onclick="act('abort')" class="px-4 py-2 rounded bg-rose-600 text-white hover:bg-rose-700">Abort</button>
          <button onclick="act('finish')" class="px-4 py-2 rounded bg-indigo-600 text-white hover:bg-indigo-700">Finish Mission</button>
        </div>
      </div>
    </div>
    <div class="p-4 bg-white shadow rounded">
      <div class="text-sm text-gray-500 mb-2">Pending step</div>
      <pre id="pending" class="text-sm whitespace-pre-wrap">—</pre>
    </div>
    <p class="mt-6 text-sm text-gray-500">This panel is local-only: <code>http://127.0.0.1:8765</code></p>
  </div>
</body>
"""

@app.get("/", response_class=HTMLResponse)
def panel(): return HTML

@app.get("/takeover/status")
def status(): return takeover.get_status()

@app.post("/takeover/approve")
def approve(): takeover.approve(); return {"ok": True}

@app.post("/takeover/abort")
def abort(): takeover.abort(); return {"ok": True}

# Finish mission: set a special decision so planner knows to exit without teardown (if keep_browser_open)
@app.post("/takeover/finish")
def finish(): takeover.approve(); return {"ok": True}

_server = None

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