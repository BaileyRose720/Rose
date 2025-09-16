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
        self.browser = await self.pw.chromium.launch_persistent_context(
            user_data_dir="runtime/edge_profile",
            headless=False
        )
        self.page = await self.browser.new_page()

    async def run(self, intent, params):
        await self._ensure()

        def _as_url(p):
            return p if isinstance(p, str) else p.get("url")
        def _as_selector(p):
            return p if isinstance(p, str) else p.get("selector")
        def _as_text(p):
            return p if isinstance(p, str) else p.get("text")

        if intent == "open_app":
            return {"ok": True}

        if intent == "navigate":
            url = _as_url(params)
            if not url:
                return {"ok": False, "error": "navigate: missing url"}
            await self.page.goto(url)
            return {"ok": True}

        if intent == "click":
            sel = _as_selector(params)
            if not sel:
                return {"ok": False, "error": "click: missing selector"}
            await self.page.click(sel)
            return {"ok": True}

        if intent == "type":
            sel = _as_selector(params)
            txt = _as_text(params)
            if not sel or txt is None:
                return {"ok": False, "error": "type: missing selector or text"}
            await self.page.fill(sel, txt)
            return {"ok": True}

        if intent == "dom":
            sel = _as_selector(params)
            script = params.get("script") if isinstance(params, dict) else None
            if not sel or not script:
                return {"ok": False, "error": "dom: missing selector or script"}
            val = await self.page.eval_on_selector(sel, script)
            return {"ok": True, "value": val}

        return {"ok": False, "error": f"unknown web intent '{intent}'"}

    async def close(self):
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