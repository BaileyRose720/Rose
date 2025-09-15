import asyncio
from playwright.async_api import async_playwright

class WebSkill:
    def __init__(self):
        self.ctx = None
        self.page = None
        self.browser = None
        self.pw = None

    async def _ensure(self):
        if self.page: return
        self.pw = await async_playwright().start()
        # Use Edge/Chromium persistent profile under runtime/
        self.browser = await self.pw.chromium.launch_persistent_context(user_data_dir="runtime/edge_profile", headless=False)
        self.page = await self.browser.new_page()

    async def run(self, intent, params):
        await self._ensure()
        if intent == "open_app":
            return {"ok": True}
        if intent == "navigate":
            await self.page.goto(params)
            return {"ok": True}
        if intent == "click":
            await self.page.click(params["selector"])
            return {"ok": True}
        if intent == "type":
            await self.page.fill(params["selector"], params["text"])
            return {"ok": True}
        if intent == "dom":
            val = await self.page.eval_on_selector(params["selector"], params["script"])
            return {"ok": True, "value": val}
        return {"ok": False, "error": "unknown web intent"}

    async def close(self):
        # close playwright resources cleanly (prevents Windows asyncio warnings)
        try:
            if self.page:
                await self.page.close()
        finally:
            try:
                if self.browser:
                    await self.browser.close()
            finally:
                if self.pw:
                    await self.pw.stop()
