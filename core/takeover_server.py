# core/takeover_server.py
import asyncio
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

app = FastAPI()

# simple decision queue for approvals
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
          async function approve() {{
            await fetch('/approve', {{method:'POST'}});
            location.reload();
          }}
          async function cancel() {{
            await fetch('/cancel', {{method:'POST'}});
            location.reload();
          }}
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

async def run_takeover_server(port: int = 8765):
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    await server.serve()