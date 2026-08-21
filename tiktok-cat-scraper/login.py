"""
One-time interactive login. Opens a real, visible browser window so you can
log into TikTok manually (including any 2FA/captcha). The resulting session
(cookies + local storage) is saved to auth_state.json and reused by
scraper.py — you should not need to log in again unless the session expires
or TikTok logs you out.

Run this on your own machine (it needs a display), not in a headless
server/container.
"""

import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

AUTH_STATE_PATH = Path(__file__).parent / "auth_state.json"


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto("https://www.tiktok.com/login")

        print("A browser window has opened.")
        print("Log into your TikTok account manually.")
        input("Once you're logged in and see your feed, press Enter here...")

        await context.storage_state(path=str(AUTH_STATE_PATH))
        print(f"Session saved to {AUTH_STATE_PATH}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
