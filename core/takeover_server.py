# core/takeover_server.py
import asyncio
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

app = FastAPI()

# --- approval state ---
_decision_queue: asyncio.Queue[bool] = asyncio.Queue()
_pending_text: str | None = None

@app.get("/", response_class=HTMLResponse)
def home():
    text = _pending_text or "Nothing pending."
    return f"""
    <html>
      <head><title>Rose Takeover</title></head>
      <body style="font-family: system-ui; max-width: 640px; margin: 48px auto;">
        <h2>Rose — Takeover</h2>
        <p id="pending">{text}</p>
        <button onclick="approve()">Approve</button>
        <button onclick="cancel()">Cancel</button>
        <script>
          async function approve() {{ await fetch('/approve', {{method:'POST'}}); }}
          async function cancel()  {{ await fetch('/cancel',  {{method:'POST'}}); }}
          setInterval(async () => {{
            const res = await fetch('/status');
            const j = await res.json();
            document.getElementById('pending').innerText = j.pending || "Nothing pending.";
          }}, 1000);
        </script>
      </body>
    </html>
    """

@app.get("/status")
def status():
    return JSONResponse({"pending": _pending_text})

@app.post("/approve")
async def approve():
    global _pending_text
    _pending_text = None
    await _decision_queue.put(True)
    return {"ok": True}

@app.post("/cancel")
async def cancel():
    global _pending_text
    _pending_text = None
    await _decision_queue.put(False)
    return {"ok": True}

async def request_decision(prompt: str = "Proceed?") -> bool:
    """Planner calls this to pause until you click Approve/Cancel in the UI."""
    global _pending_text
    _pending_text = prompt
    decision = await _decision_queue.get()
    return decision

# --- server lifecycle helpers ---

_server_task: asyncio.Task | None = None

async def _serve(port: int = 8765):
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    await server.serve()

async def start_takeover_server(port: int = 8765):
    """Background-start the takeover server. Safe to call once."""
    global _server_task
    if _server_task is None or _server_task.done():
        _server_task = asyncio.create_task(_serve(port))
    return True

async def stop_takeover_server():
    """Stop the takeover server if running."""
    global _server_task
    if _server_task:
        _server_task.cancel()
        try:
            await _server_task
        except Exception:
            pass
        _server_task = None

# Back-compat if something elsewhere imports this name:
async def run_takeover_server(port: int = 8765):
    await _serve(port)