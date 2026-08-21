"""
Searches TikTok for cat-related trends (funny cats, fat cats, etc.) using a
logged-in browser session, collects video links, and keeps a local dedup
store so already-seen videos are never re-added.

Requires auth_state.json (see login.py) to already exist.
"""

import asyncio
import json
import random
import re
from datetime import datetime, timezone
from pathlib import Path

from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).parent
AUTH_STATE_PATH = BASE_DIR / "auth_state.json"
CONFIG_PATH = BASE_DIR / "config.json"
SAVED_VIDEOS_PATH = BASE_DIR / "saved_videos.json"

VIDEO_LINK_RE = re.compile(r"tiktok\.com/@([\w.\-]+)/video/(\d+)")


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def load_saved_videos():
    if SAVED_VIDEOS_PATH.exists():
        with open(SAVED_VIDEOS_PATH) as f:
            return json.load(f)
    return {}


def save_videos(videos):
    with open(SAVED_VIDEOS_PATH, "w") as f:
        json.dump(videos, f, indent=2, ensure_ascii=False)


def extract_from_search_payload(payload):
    """Best-effort extraction of video info from a TikTok search API JSON
    response. TikTok's internal schema shifts over time, so this only
    assumes a loose shape and skips anything it can't confidently parse."""
    results = []
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, list):
        return results

    for item in data:
        video = item.get("item") or item.get("aweme_info") if isinstance(item, dict) else None
        if not isinstance(video, dict):
            continue
        video_id = video.get("id") or video.get("aweme_id")
        author_info = video.get("author") or {}
        author = author_info.get("uniqueId") or author_info.get("unique_id")
        if not video_id or not author:
            continue
        results.append({
            "id": str(video_id),
            "url": f"https://www.tiktok.com/@{author}/video/{video_id}",
            "author": author,
            "description": video.get("desc", ""),
        })
    return results


async def extract_from_dom(page):
    """Fallback: scrape video links directly out of the rendered page.
    Less rich than the API payload (no description) but more resilient to
    TikTok changing its internal JSON schema."""
    hrefs = await page.eval_on_selector_all(
        "a[href*='/video/']",
        "elements => elements.map(e => e.href)",
    )
    results = []
    for href in hrefs:
        m = VIDEO_LINK_RE.search(href)
        if not m:
            continue
        author, video_id = m.group(1), m.group(2)
        results.append({
            "id": video_id,
            "url": f"https://www.tiktok.com/@{author}/video/{video_id}",
            "author": author,
            "description": "",
        })
    return results


async def search_term(page, term, max_scrolls, delay_range):
    collected = {}

    async def on_response(response):
        if "/api/search/" not in response.url:
            return
        try:
            payload = await response.json()
        except Exception:
            return
        for video in extract_from_search_payload(payload):
            collected.setdefault(video["id"], video)

    page.on("response", on_response)

    search_url = f"https://www.tiktok.com/search/video?q={term}"
    await page.goto(search_url, wait_until="networkidle")
    await asyncio.sleep(random.uniform(*delay_range))

    for _ in range(max_scrolls):
        await page.mouse.wheel(0, random.randint(1500, 2500))
        await asyncio.sleep(random.uniform(*delay_range))

    for video in await extract_from_dom(page):
        collected.setdefault(video["id"], video)

    page.remove_listener("response", on_response)
    return list(collected.values())


async def run():
    config = load_config()
    saved_videos = load_saved_videos()
    new_videos = []
    delay_range = tuple(config.get("delay_range_seconds", [2, 5]))

    if not AUTH_STATE_PATH.exists():
        raise SystemExit(
            "No auth_state.json found. Run `python login.py` first to log into TikTok."
        )

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=config.get("headless", True))
        context = await browser.new_context(storage_state=str(AUTH_STATE_PATH))
        page = await context.new_page()

        for term in config["search_terms"]:
            print(f"Searching: {term}")
            found = await search_term(page, term, config.get("max_scrolls", 4), delay_range)

            added = 0
            for video in found:
                if video["id"] in saved_videos:
                    continue
                video["matched_term"] = term
                video["found_at"] = datetime.now(timezone.utc).isoformat()
                saved_videos[video["id"]] = video
                new_videos.append(video)
                added += 1
            print(f"  found {len(found)} videos, {added} new")

            await asyncio.sleep(random.uniform(*delay_range))

        await context.storage_state(path=str(AUTH_STATE_PATH))
        await browser.close()

    save_videos(saved_videos)

    print(f"\nDone. {len(new_videos)} new videos added, {len(saved_videos)} total saved.")
    if new_videos:
        print("\nNew links:")
        for v in new_videos:
            print(f"  {v['url']}  ({v['matched_term']})")


if __name__ == "__main__":
    asyncio.run(run())
