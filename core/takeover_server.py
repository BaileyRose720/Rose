# core/takeover_server.py
import asyncio
from fastapi import FastAPI, Body
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

app = FastAPI()
_current_mode = "autonomous"
_panic_flag = asyncio.Event()

@app.post("/mode")
def set_mode(payload: dict = Body(...)):
    global _current_mode
    m = (payload.get("mode") or "").lower()
    if m not in ("autonomous","cautious","strict"):
        return JSONResponse({"ok": False, "error": "mode must be autonomous|cautious|strict"}, status_code=400)
    _current_mode = m
    # Also reflect into the policy file if you want persistence (not shown)
    return {"ok": True, "mode": _current_mode}

@app.get("/mode")
def get_mode():
    return {"mode": _current_mode}

def current_mode() -> str:
    return _current_mode

@app.post("/panic")
async def panic():
    _panic_flag.set()
    return {"ok": True}

# Planner can poll this between steps if you want hard-stop-on-demand:
def panic_requested() -> bool:
    return _panic_flag.is_set()

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
    global _pending_text
    _pending_text = prompt
    decision = await _decision_queue.get()
    return decision

# --- server lifecycle helpers (graceful) ---
_server_task: asyncio.Task | None = None
_server: uvicorn.Server | None = None

async def _serve(port: int = 8765):
    global _server
    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=port,
        log_level="warning",
        lifespan="off",           # <— avoid lifespan CancelledError noise
    )
    _server = uvicorn.Server(config)
    await _server.serve()

async def start_takeover_server(port: int = 8765):
    global _server_task
    if _server_task is None or _server_task.done():
        _server_task = asyncio.create_task(_serve(port))
    return True

async def stop_takeover_server():
    global _server_task, _server
    # Tell server to exit cleanly
    if _server is not None:
        _server.should_exit = True
    # Await task with timeout; only cancel if it hangs
    if _server_task:
        try:
            await asyncio.wait_for(_server_task, timeout=2.0)
        except asyncio.TimeoutError:
            _server_task.cancel()
            with contextlib.suppress(Exception):
                await _server_task
        finally:
            _server_task = None
            _server = None

# Back-compat
async def run_takeover_server(port: int = 8765):
    await _serve(port)

# needed import
import contextlib