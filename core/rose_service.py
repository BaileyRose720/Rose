import asyncio, sys, contextlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # C:\RoseAI
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.takeover_server import start_takeover_server, stop_takeover_server

async def main():
    await start_takeover_server(port=8765)
    try:
        while True:
            await asyncio.sleep(3600)
    finally:
            await stop_takeover_server()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)