import os
import re
from typing import Optional, Dict, Any, Callable

from playwright.async_api import async_playwright, TimeoutError as PWTimeout

AUTH_PATH = r"C:\RoseAI\.auth\outlook.json"
DEBUG_DIR = r"C:\RoseAI\.debug"
os.makedirs(os.path.dirname(AUTH_PATH), exist_ok=True)
os.makedirs(DEBUG_DIR, exist_ok=True)

OWA_COMPOSE_URLS = [
    # Microsoft 365 work/school
    "https://outlook.office.com/mail/deeplink/compose",
    "https://outlook.office.com/mail/",
    # Personal Microsoft accounts (Outlook/Hotmail)
    "https://outlook.live.com/mail/0/deeplink/compose",
    "https://outlook.live.com/mail/",
]


class PlaywrightWeb:
    """
    Minimal web skill with a single .run(action, params) entrypoint.
    Supports:
      - goto {url}
      - wait_for {selector, timeout_ms}
      - fill {selector, text}
      - press {selector, key}
      - click {selector? role? name?}
      - type_into_contenteditable {selector, text}
      - outlook_compose {to, subject, body, cc?, bcc?, send_now?}
      - screenshot {path?}
      - close
    """

    def __init__(self):
        self._started = False
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    async def _ensure_started(self):
        if self._started:
            return
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        storage = AUTH_PATH if os.path.exists(AUTH_PATH) else None
        self.context = await self.browser.new_context(storage_state=storage)
        self.page = await self.context.new_page()
        self._started = True

    async def close(self):
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
        finally:
            if self.playwright:
                await self.playwright.stop()
            self._started = False

    # ------------ Outlook helpers ------------

    async def _open_outlook_compose(self):
        # Try deeplink first, then fall back to mailbox + "New mail"
        for url in OWA_COMPOSE_URLS:
            await self.page.goto(url)
            try:
                compose = self.page.locator(
                    "div[aria-label*='New message'], div[aria-label='Message']"
                )
                await compose.first.wait_for(state="visible", timeout=8000)
                return compose.first
            except PWTimeout:
                pass

        # We’re probably in mailbox – click “New mail”
        new_btn = self.page.get_by_role(
            "button",
            name=re.compile(r"^(New|New Mail|New message)$", re.I),
        )
        if await new_btn.count():
            await new_btn.first.click()
        else:
            alt_new = self.page.locator("[data-automationid='NewMessage']")
            await alt_new.first.click()

        compose = self.page.locator("div[aria-label*='New message'], div[aria-label='Message']")
        await compose.first.wait_for(state="visible", timeout=15000)
        return compose.first

    async def _fill_outlook_recipients(self, compose, to_text: str,
                                       cc_text: Optional[str] = None,
                                       bcc_text: Optional[str] = None):
        to_input = compose.locator(
            "input[aria-label='To'], div[aria-label='To'] input, "
            "div[aria-label='To'] [role='combobox'] input, [role='group'][aria-label='To'] input"
        )
        await to_input.first.wait_for(state="visible", timeout=15000)
        await to_input.first.fill(to_text)
        # Press Enter to commit chips
        await to_input.first.press("Enter")

        async def _open_and_fill(field_label: str, value: str):
            toggle = compose.get_by_role("button", name=lambda n: n and field_label.lower() in n.lower())
            if await toggle.count():
                await toggle.first.click()
            field = compose.locator(
                f"input[aria-label='{field_label}'], div[aria-label='{field_label}'] input, "
                f"[role='group'][aria-label='{field_label}'] input"
            )
            await field.first.wait_for(state="visible", timeout=8000)
            await field.first.fill(value)
            await field.first.press("Enter")

        if cc_text:
            await _open_and_fill("Cc", cc_text)
        if bcc_text:
            await _open_and_fill("Bcc", bcc_text)

    async def _fill_outlook_subject(self, compose, subject_text: str):
        subject = compose.locator(
            "input[aria-label='Add a subject'], input[placeholder='Add a subject'], "
            "input[aria-label='Subject'], [role='textbox'][aria-label='Subject']"
        )
        await subject.first.wait_for(state="visible", timeout=15000)
        await subject.first.fill(subject_text)

    async def _fill_outlook_body(self, compose, body_text: str):
        body = compose.locator(
            "div[aria-label='Message body'][contenteditable='true'], "
            'div[role="textbox"][contenteditable="true"]'
        )
        await body.first.wait_for(state="visible", timeout=15000)
        await body.first.click()
        await compose.page.keyboard.insert_text(body_text)

    async def _click_outlook_send(self, compose):
        send = compose.get_by_role("button", name=re.compile(r"^Send$", re.I))
        if not await send.count():
            send = compose.locator("[data-automationid='SplitButtonPrimaryAction'], [data-automationid='send']")
        await send.first.wait_for(state="visible", timeout=10000)
        await send.first.click()

    async def compose_and_send_outlook(self, to: str, subject: str, body: str,
                                       cc: Optional[str] = None,
                                       bcc: Optional[str] = None,
                                       send_now: bool = False):
        compose = None
        try:
            compose = await self._open_outlook_compose()
            # Quick auth guard
            if "login.microsoftonline.com" in self.page.url or "signin" in self.page.url:
                raise RuntimeError(
                    "Not signed in to Outlook. Re-run your auth saver to refresh: save_outlook_auth.py"
                )

            await self._fill_outlook_recipients(compose, to, cc, bcc)
            await self._fill_outlook_subject(compose, subject)
            await self._fill_outlook_body(compose, body)

            if send_now:
                await self._click_outlook_send(compose)
                # Optional: wait for a "Sent" toast/snackbar
                toast = self.page.get_by_text(lambda t: t and "sent" in t.lower())
                try:
                    await toast.first.wait_for(timeout=8000)
                except PWTimeout:
                    pass  # Not all tenants show this reliably

            return {"ok": True}
        except PWTimeout as e:
            snap = os.path.join(DEBUG_DIR, "outlook_draft_failure.png")
            await self.page.screenshot(path=snap, full_page=True)
            raise RuntimeError(f"Outlook compose timed out at {self.page.url}. Screenshot: {snap}\n{e}") from e
        except Exception as e:
            snap = os.path.join(DEBUG_DIR, "outlook_draft_error.png")
            try:
                await self.page.screenshot(path=snap, full_page=True)
            except Exception:
                snap = "(screenshot failed)"
            raise RuntimeError(f"Outlook compose error at {self.page.url}. Screenshot: {snap}\n{e}") from e

    # ------------ Generic action runner ------------

    async def run(self, action: str, params: Dict[str, Any]):
        await self._ensure_started()

        # Small dispatch table
        handlers: Dict[str, Callable[[Dict[str, Any]], Any]] = {
            "goto": self._act_goto,
            "wait_for": self._act_wait_for,
            "fill": self._act_fill,
            "press": self._act_press,
            "click": self._act_click,
            "type_into_contenteditable": self._act_type_into_contenteditable,
            "screenshot": self._act_screenshot,
            "outlook_compose": self._act_outlook_compose,
            "close": self._act_close,
        }

        if action not in handlers:
            raise ValueError(f"Unknown action: {action}")

        return await handlers[action](params)

    # ------------ Action implementations ------------

    async def _act_goto(self, params: Dict[str, Any]):
        url = params.get("url")
        if not url:
            raise ValueError("goto requires 'url'")
        await self.page.goto(url)
        await self.page.wait_for_load_state("domcontentloaded")
        return {"ok": True, "url": self.page.url}

    async def _act_wait_for(self, params: Dict[str, Any]):
        selector = params.get("selector")
        timeout_ms = params.get("timeout_ms", 15000)
        if not selector:
            raise ValueError("wait_for requires 'selector'")
        loc = self.page.locator(selector)
        await loc.first.wait_for(state="visible", timeout=timeout_ms)
        return {"ok": True}

    async def _act_fill(self, params: Dict[str, Any]):
        selector = params.get("selector")
        text = params.get("text", "")
        if not selector:
            raise ValueError("fill requires 'selector'")
        loc = self.page.locator(selector)
        await loc.first.wait_for(state="visible", timeout=15000)
        await loc.first.fill(text)
        return {"ok": True}

    async def _act_press(self, params: Dict[str, Any]):
        selector = params.get("selector")
        key = params.get("key")
        if not selector or not key:
            raise ValueError("press requires 'selector' and 'key'")
        loc = self.page.locator(selector)
        await loc.first.wait_for(state="visible", timeout=15000)
        await loc.first.press(key)
        return {"ok": True}

    async def _act_click(self, params: Dict[str, Any]):
        selector = params.get("selector")
        role = params.get("role")
        name = params.get("name")

        if selector:
            loc = self.page.locator(selector)
        elif role and name:
            # Supports lambda name for case-insensitive matching
            if isinstance(name, str):
                loc = self.page.get_by_role(role, name=re.compile(re.escape(name), re.I))
        elif hasattr(name, "pattern"):  # already a compiled regex
                loc = self.page.get_by_role(role, name=name)
        else:
            raise ValueError("click with role requires name as str or compiled regex")

        await loc.first.wait_for(state="visible", timeout=15000)
        await loc.first.click()
        return {"ok": True}

    async def _act_type_into_contenteditable(self, params: Dict[str, Any]):
        selector = params.get("selector")
        text = params.get("text", "")
        if not selector:
            raise ValueError("type_into_contenteditable requires 'selector'")
        loc = self.page.locator(selector)
        await loc.first.wait_for(state="visible", timeout=15000)
        await loc.first.click()
        await self.page.keyboard.insert_text(text)
        return {"ok": True}

    async def _act_screenshot(self, params: Dict[str, Any]):
        path = params.get("path", os.path.join(DEBUG_DIR, "shot.png"))
        await self.page.screenshot(path=path, full_page=True)
        return {"ok": True, "path": path}

    async def _act_outlook_compose(self, params: Dict[str, Any]):
        to = params.get("to")
        subject = params.get("subject", "")
        body = params.get("body", "")
        cc = params.get("cc")
        bcc = params.get("bcc")
        send_now = bool(params.get("send_now", False))
        if not to:
            raise ValueError("outlook_compose requires 'to'")
        return await self.compose_and_send_outlook(to, subject, body, cc, bcc, send_now)

    async def _act_close(self, _params: Dict[str, Any]):
        await self.close()
        return {"ok": True}
    
class WebSkill(PlaywrightWeb):
        """Alias to satisfy `from skills.general.playwright_web import WebSkill`."""
        pass

__all__ = ["WebSkill"]