import asyncio
from typing import Optional, Dict, Any

class Takeover:
    def __init__(self):
        self._event = asyncio.Event()
        self._decision: Optional[str] = None
        self._pending: Optional[Dict[str, Any]] = None

    def set_pending(self, step: Dict[str, Any]):
        self._pending = step
        self._decision = None
        self._event.clear()

    def clear(self):
        self._pending = None
        self._decision = None
        self._event.clear()

    async def wait(self) -> str:
        await self._event.wait()
        return self._decision or "approve"

    def approve(self):
        self._decision = "approve"
        self._event.set()

    def abort(self):
        self._decision = "abort"
        self._event.set()

    def get_status(self):
        return {
            "pending": self._pending,
            "decision": self._decision,
            "waiting": not self._event.is_set() if self._pending else False,
        }

takeover = Takeover()