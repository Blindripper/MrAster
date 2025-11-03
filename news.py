#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parametrisierte, rückwärtskompatible WLFI/X-Scraper-Version.

• Standardverhalten identisch mit der alten Version (wenn ohne Args gestartet):
  - Suche: "WLFI" (Top)
  - Cookies: xAuth.json
  - Limit/Scroll/Delays wie zuvor
  - Output: wlfi_tweets.json (+ optional HTML-Dump)
• Neue Parameter (optional):
  --query "WLFI, USD1"          # mehrere, komma-getrennt
  --feed top|live                # Top (default) oder Neu (Latest)
  --tweet-limit 50               # Anzahl Tweets anvisiert (pro Query aggregiert)
  --scroll-delay 2.0             # Sekunden zwischen Scrolls
  --scroll-attempts 30           # wie oft nachgeladen wird
  --cookies xAuth.json           # Pfad zur Cookie-Datei
  --out wlfi_tweets.json         # Output JSON-Datei
  --html-dump wlfi_full_result.html  # optionaler HTML-Dump (leer lassen = kein Dump)
"""

import asyncio
import argparse
import json
from pathlib import Path
from typing import List
from playwright.async_api import async_playwright

# ------------------------------
# Defaults (rückwärtskompatibel)
# ------------------------------
DEF_QUERY = "WLFI"
DEF_FEED = "top"  # "top" (Top) oder "live" (Neu/Latest)
DEF_COOKIES = "xAuth.json"
DEF_TWEET_LIMIT = 50
DEF_SCROLL_DELAY = 2.0
DEF_SCROLL_ATTEMPTS = 30
DEF_OUT = "wlfi_tweets.json"
DEF_HTML_DUMP = "wlfi_full_result.html"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Twitter/X Scraper (Playwright)")
    p.add_argument("--query", default=DEF_QUERY,
                   help="Suchbegriffe, kommasepariert (z.B. 'WLFI, USD1')")
    p.add_argument("--feed", choices=["top", "live"], default=DEF_FEED,
                   help="'top' (Top) oder 'live' (Neu/Latest)")
    p.add_argument("--tweet-limit", type=int, default=DEF_TWEET_LIMIT)
    p.add_argument("--scroll-delay", type=float, default=DEF_SCROLL_DELAY,
                   help="Sekunden zwischen Scrolls")
    p.add_argument("--scroll-attempts", type=int, default=DEF_SCROLL_ATTEMPTS)
    p.add_argument("--cookies", default=DEF_COOKIES)
    p.add_argument("--out", default=DEF_OUT)
    p.add_argument("--html-dump", default=DEF_HTML_DUMP,
                   help="Pfad für HTML-Dump oder leer lassen für keinen Dump")
    return p.parse_args()


async def load_cookies(path: str) -> List[dict]:
    with open(path, "r", encoding="utf-8") as f:
        cookies = json.load(f)
    for cookie in cookies:
        if "sameSite" not in cookie or cookie["sameSite"] not in ["Strict", "Lax", "None"]:
            cookie["sameSite"] = "Lax"
    return cookies


async def scrape_query(context, query: str, feed: str, limit: int, delay: float, attempts: int) -> list:
    page = await context.new_page()
    base = f"https://twitter.com/search?q={query}&src=typed_query"
    url = base if feed == "top" else base + "&f=live"
    print(f"🌐 {query} → {url}")
    await page.goto(url)
    await page.wait_for_timeout(3000)

    tweet_texts = set()
    scrolls = 0
    print("📜 Scrolle und sammle Tweets…")
    while len(tweet_texts) < limit and scrolls < attempts:
        nodes = await page.query_selector_all("article div[lang]")
        for n in nodes:
            try:
                text = await n.inner_text()
            except Exception:
                continue
            if text and text.strip():
                tweet_texts.add(text.strip())
                if len(tweet_texts) >= limit:
                    break
        scrolls += 1
        await page.mouse.wheel(0, 2000)
        await page.wait_for_timeout(int(delay * 1000))
        print(f"↪️  Scroll #{scrolls} – {len(tweet_texts)} Tweets gesammelt…")

    await page.close()
    return list(tweet_texts)


async def run():
    args = parse_args()
    queries = [q.strip() for q in args.query.split(",") if q.strip()]
    all_texts = []

    print("🔄 Starte Browser…")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        try:
            cookies = await load_cookies(args.cookies)
            await context.add_cookies(cookies)
            print(f"🔐 {len(cookies)} Cookies gesetzt.")
        except FileNotFoundError:
            print(f"⚠️  Cookie-Datei nicht gefunden: {args.cookies} – es wird ohne Login versucht.")

        for q in queries:
            texts = await scrape_query(context, q, args.feed, args.tweet_limit, args.scroll_delay, args.scroll_attempts)
            all_texts.extend(texts)

        # Optional: HTML-Dump der letzten Seite
        if args.html_dump:
            try:
                page = await context.new_page()
                await page.goto("https://twitter.com/explore")
                html = await page.content()
                Path(args.html_dump).write_text(html, encoding="utf-8")
                await page.close()
                print(f"📝 HTML-Dump: {args.html_dump}")
            except Exception as e:
                print(f"⚠️  HTML-Dump fehlgeschlagen: {e}")

        Path(args.out).write_text(json.dumps(all_texts, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"💾 Exportiert nach {args.out}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(run())
