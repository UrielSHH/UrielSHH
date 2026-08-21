# TikTok Cat Video Scraper

Searches TikTok for cat-related trends (funny cats, fat cats, cute cats,
etc.), collects video links, and keeps a local list so you can browse them
later without duplicates.

This uses browser automation with your own logged-in TikTok session, since
TikTok's official API does not allow keyword/hashtag search for personal
apps (only an approved-researcher "Research API" supports that, and a
regular "Content Posting" API that only sees your own account). **This
means it relies on unofficial, reverse-engineered access, which violates
TikTok's Terms of Service and carries a real risk of your account being
rate-limited, flagged, or suspended.** Use at your own risk, and keep usage
light (see "Staying under the radar" below).

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   playwright install chromium
   ```
2. Log in once (opens a real browser window — run this on a machine with a
   display, not a headless server):
   ```
   python login.py
   ```
   Log into your TikTok account in the window that opens, then press Enter
   in the terminal. This saves your session to `auth_state.json`.
3. Edit `config.json` to adjust search terms, scroll count, or delays.
4. Run the scraper:
   ```
   python scraper.py
   ```

## How it works

- For each search term in `config.json`, it opens TikTok's search page and
  scrolls a few times, like a person browsing.
- It reads video links both from TikTok's search API responses (richer
  data) and directly from the page (fallback, in case TikTok changes its
  internal API shape).
- Every video is keyed by its TikTok video ID in `saved_videos.json`.
  Videos already in that file are skipped on future runs, so re-running the
  script only adds new finds.
- `saved_videos.json` stores: link, author, description, which search term
  matched, and when it was found.

## Staying under the radar

There's no way to make unofficial access undetectable, but you can lower
risk:
- Don't run it constantly or on a tight schedule — a few times a day at
  most, at irregular times.
- Keep `max_scrolls` and the number of search terms modest per run.
- Keep the randomized delays in `config.json` (`delay_range_seconds`) —
  don't set them to 0.
- Use the same account for normal TikTok browsing too, so its activity
  doesn't look purely automated.

## Files that are never committed

`auth_state.json` (your login session) and `saved_videos.json` (your
personal collected data) are both git-ignored. `auth_state.json` in
particular is equivalent to your TikTok login — never share or commit it.
