# core/takeover_server.py
import asyncio
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/health")
def health():
    return {"ok": True}

_server: uvicorn.Server | None = None

async def start_takeover_server(port: int = 8765):
    """Start uvicorn server in-process and return immediately."""
    global _server
    if _server:
        return _server
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning", lifespan="off")
    _server = uvicorn.Server(config)
    # run serve() in the background
    asyncio.create_task(_server.serve())
    # wait until the server is started (briefly poll)
    for _ in range(50):
        if _server.started:  # available on recent uvicorn
            break
        await asyncio.sleep(0.05)
    return _server

async def stop_takeover_server():
    """Politely ask uvicorn to exit; avoid CancelledError noise on Windows."""
    global _server
    if _server:
        _server.should_exit = True
        # give it a tick to unwind
        for _ in range(50):
            if _server.lifespan is None or _server.started is False:
                break
            await asyncio.sleep(0.05)
        _server = None