# tools/save_outlook_auth.py

import asyncio, os
from playwright.async_api import async_playwright 

AUTH_PATH = r"C:\RoseAI\.auth\outlook.json"

async def main():
    os.makedirs(r"C:\RoseAI\.auth", exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto ("https://outlook.live.com/mail/")

        print("Sign in to Outlook completely (finish 2FA if prompted), then press Enter here...")
        input()
        await context.storage_state(path=AUTH_PATH)
        print(f"Save auth state to {AUTH_PATH}")
        await browser.close()

asyncio.run(main())