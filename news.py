#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Utility helpers to scrape X (Twitter) posts for use inside the trading bot.

The file keeps the standalone CLI behaviour of the legacy ``news.py`` script but
also exposes a small, caching friendly API that can be imported from the bot.

Typical usage from code::

    from news import NewsScraper

    scraper = NewsScraper(cookies_path="xAuth.json")
    posts = scraper.fetch("BTCUSDT")

The script requires a valid ``xAuth.json`` exported from an authenticated
browser session.  Playwright must also be installed in the environment.  When
invoked as CLI a JSON file with either the raw tweet texts (legacy mode) or a
rich structure containing metadata is written to disk.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import re
import threading
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union, Set

from urllib.parse import quote_plus, urljoin

try:  # Optional dependency – resolved lazily for environments without Playwright
    from playwright.async_api import async_playwright
except Exception as exc:  # pragma: no cover - import guard
    async_playwright = None  # type: ignore
    _PLAYWRIGHT_IMPORT_ERROR = exc
else:  # pragma: no cover - import guard
    _PLAYWRIGHT_IMPORT_ERROR = None

log = logging.getLogger("news")

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
DEF_CACHE_TTL = 15 * 60.0


class NewsScraperError(RuntimeError):
    """Raised when scraping fails due to missing dependencies or runtime errors."""


@dataclass(frozen=True)
class ScrapedPost:
    """Normalized representation of a tweet/post returned by the scraper."""

    text: str
    url: Optional[str] = None
    author: Optional[str] = None
    handle: Optional[str] = None
    timestamp: Optional[str] = None
    lang: Optional[str] = None
    likes: Optional[int] = None
    retweets: Optional[int] = None
    replies: Optional[int] = None
    query: Optional[str] = None

    def to_dict(self) -> Dict[str, Optional[Any]]:
        return {
            "text": self.text,
            "url": self.url,
            "author": self.author,
            "handle": self.handle,
            "timestamp": self.timestamp,
            "lang": self.lang,
            "likes": self.likes,
            "retweets": self.retweets,
            "replies": self.replies,
            "query": self.query,
        }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="X/Twitter Scraper (Playwright)")
    p.add_argument(
        "--query",
        default=DEF_QUERY,
        help="Suchbegriffe, kommasepariert (z.B. 'WLFI, USD1')",
    )
    p.add_argument(
        "--feed",
        choices=["top", "live"],
        default=DEF_FEED,
        help="'top' (Top) oder 'live' (Neu/Latest)",
    )
    p.add_argument("--tweet-limit", type=int, default=DEF_TWEET_LIMIT)
    p.add_argument(
        "--scroll-delay",
        type=float,
        default=DEF_SCROLL_DELAY,
        help="Sekunden zwischen Scrolls",
    )
    p.add_argument("--scroll-attempts", type=int, default=DEF_SCROLL_ATTEMPTS)
    p.add_argument("--cookies", default=DEF_COOKIES)
    p.add_argument("--out", default=DEF_OUT)
    p.add_argument(
        "--html-dump",
        default=DEF_HTML_DUMP,
        help="Pfad für HTML-Dump oder leer lassen für keinen Dump",
    )
    p.add_argument(
        "--rich-json",
        action="store_true",
        help="Ausgabe der erweiterten Struktur (Texte + Metadaten).",
    )
    return p.parse_args()


def _ensure_playwright_available() -> None:
    if async_playwright is None:
        raise NewsScraperError(
            "Playwright ist nicht installiert. Bitte 'pip install playwright' ausführen "
            "und anschließend 'playwright install'."
        ) from _PLAYWRIGHT_IMPORT_ERROR


def _parse_number(value: Optional[str]) -> Optional[int]:
    if not value:
        return None
    match = re.search(r"([0-9]+(?:[.,][0-9]+)?)([KMB]?)", value)
    if not match:
        return None
    number = match.group(1).replace(",", "")
    try:
        count = float(number)
    except ValueError:
        return None
    suffix = match.group(2)
    if suffix == "K":
        count *= 1_000
    elif suffix == "M":
        count *= 1_000_000
    elif suffix == "B":
        count *= 1_000_000_000
    return int(count)


async def load_cookies(path: str) -> List[dict]:
    with open(path, "r", encoding="utf-8") as f:
        cookies = json.load(f)
    for cookie in cookies:
        if "sameSite" not in cookie or cookie["sameSite"] not in ["Strict", "Lax", "None"]:
            cookie["sameSite"] = "Lax"
    return cookies


async def _extract_post(article) -> Optional[ScrapedPost]:
    text_node = await article.query_selector("div[lang]")
    if text_node is None:
        return None
    try:
        text = (await text_node.inner_text()).strip()
    except Exception:
        return None
    if not text:
        return None

    lang = await text_node.get_attribute("lang")

    handle = None
    author = None
    user_nodes = await article.query_selector_all("div[data-testid='User-Name'] span")
    for node in user_nodes:
        try:
            content = (await node.inner_text()).strip()
        except Exception:
            continue
        if content.startswith("@") and not handle:
            handle = content
        elif not author:
            author = content
        if author and handle:
            break

    url = None
    link_node = await article.query_selector("a[href*='/status/'][role='link']")
    if link_node:
        href = await link_node.get_attribute("href")
        if href:
            url = urljoin("https://twitter.com", href)

    timestamp = None
    time_node = await article.query_selector("time")
    if time_node:
        timestamp = await time_node.get_attribute("datetime")

    metrics = {"likes": None, "retweets": None, "replies": None}
    for key, test_id in ("replies", "reply"), ("retweets", "retweet"), ("likes", "like"):
        metric_node = await article.query_selector(f"div[data-testid='{test_id}']")
        if metric_node:
            aria_label = await metric_node.get_attribute("aria-label")
            metrics[key] = _parse_number(aria_label)

    return ScrapedPost(
        text=text,
        url=url,
        author=author,
        handle=handle,
        timestamp=timestamp,
        lang=lang,
        likes=metrics["likes"],
        retweets=metrics["retweets"],
        replies=metrics["replies"],
    )


async def scrape_query(context, query: str, feed: str, limit: int, delay: float, attempts: int) -> List[ScrapedPost]:
    page = await context.new_page()
    base = f"https://twitter.com/search?q={quote_plus(query)}&src=typed_query"
    url = base if feed == "top" else base + "&f=live"
    log.debug("🌐 %s → %s", query, url)
    await page.goto(url, wait_until="domcontentloaded")
    await page.wait_for_timeout(3000)

    collected: List[ScrapedPost] = []
    seen: Set[str] = set()
    scrolls = 0
    while len(collected) < limit and scrolls < attempts:
        nodes = await page.query_selector_all("article[data-testid='tweet']")
        for article in nodes:
            try:
                post = await _extract_post(article)
            except Exception:
                continue
            if not post:
                continue
            key = post.url or post.text
            if key in seen:
                continue
            seen.add(key)
            collected.append(replace(post, query=query))
            if len(collected) >= limit:
                break
        scrolls += 1
        if len(collected) >= limit:
            break
        await page.mouse.wheel(0, 2000)
        await page.wait_for_timeout(int(delay * 1000))
    await page.close()
    return collected


async def scrape_queries_async(
    queries: Sequence[str],
    *,
    feed: str = DEF_FEED,
    tweet_limit: int = DEF_TWEET_LIMIT,
    scroll_delay: float = DEF_SCROLL_DELAY,
    scroll_attempts: int = DEF_SCROLL_ATTEMPTS,
    cookies_path: str = DEF_COOKIES,
    html_dump: Optional[str] = None,
) -> Dict[str, List[Dict[str, Optional[Any]]]]:
    _ensure_playwright_available()
    normalized = [q.strip() for q in queries if q and q.strip()]
    if not normalized:
        return {}
    async with async_playwright() as p:  # type: ignore[misc]
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        try:
            cookies = await load_cookies(cookies_path)
        except FileNotFoundError:
            log.warning("Cookie-Datei nicht gefunden: %s – es wird ohne Login versucht.", cookies_path)
        else:
            await context.add_cookies(cookies)
            log.debug("%d Cookies gesetzt.", len(cookies))

        results: Dict[str, List[Dict[str, Optional[Any]]]] = {}
        for query in normalized:
            posts = await scrape_query(context, query, feed, tweet_limit, scroll_delay, scroll_attempts)
            results[query] = [post.to_dict() for post in posts]

        if html_dump:
            try:
                page = await context.new_page()
                await page.goto("https://twitter.com/explore")
                html = await page.content()
                Path(html_dump).write_text(html, encoding="utf-8")
                await page.close()
                log.debug("HTML-Dump gespeichert: %s", html_dump)
            except Exception as exc:
                log.warning("HTML-Dump fehlgeschlagen: %s", exc)

        await browser.close()
    return results


def _run_async(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    result: Dict[str, Any] = {}

    def _runner():
        new_loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(new_loop)
            result["value"] = new_loop.run_until_complete(coro)
        except Exception as exc:  # pragma: no cover - executed rarely
            result["error"] = exc
        finally:
            asyncio.set_event_loop(None)
            new_loop.close()

    thread = threading.Thread(target=_runner, daemon=True)
    thread.start()
    thread.join()
    if "error" in result:
        raise result["error"]
    return result.get("value")


def scrape_queries(
    queries: Sequence[str],
    *,
    feed: str = DEF_FEED,
    tweet_limit: int = DEF_TWEET_LIMIT,
    scroll_delay: float = DEF_SCROLL_DELAY,
    scroll_attempts: int = DEF_SCROLL_ATTEMPTS,
    cookies_path: str = DEF_COOKIES,
    html_dump: Optional[str] = None,
) -> Dict[str, List[Dict[str, Optional[Any]]]]:
    """Synchronously scrape tweets for the given ``queries``.

    The helper is a thin wrapper around :func:`scrape_queries_async` that also
    works when the caller already owns an active asyncio event loop.
    """

    return _run_async(
        scrape_queries_async(
            queries,
            feed=feed,
            tweet_limit=tweet_limit,
            scroll_delay=scroll_delay,
            scroll_attempts=scroll_attempts,
            cookies_path=cookies_path,
            html_dump=html_dump,
        )
    )  # type: ignore[return-value]


def fetch_top_posts(
    query: str,
    *,
    feed: str = DEF_FEED,
    tweet_limit: int = DEF_TWEET_LIMIT,
    scroll_delay: float = DEF_SCROLL_DELAY,
    scroll_attempts: int = DEF_SCROLL_ATTEMPTS,
    cookies_path: str = DEF_COOKIES,
) -> List[Dict[str, Optional[Any]]]:
    """Fetch posts for a single query in a synchronous manner."""

    result = scrape_queries(
        [query],
        feed=feed,
        tweet_limit=tweet_limit,
        scroll_delay=scroll_delay,
        scroll_attempts=scroll_attempts,
        cookies_path=cookies_path,
    )
    return result.get(query, [])


class NewsScraper:
    """Convenience wrapper with caching for repeated bot usage."""

    def __init__(
        self,
        *,
        cookies_path: str = DEF_COOKIES,
        feed: str = DEF_FEED,
        tweet_limit: int = DEF_TWEET_LIMIT,
        scroll_delay: float = DEF_SCROLL_DELAY,
        scroll_attempts: int = DEF_SCROLL_ATTEMPTS,
        cache_ttl: float = DEF_CACHE_TTL,
    ) -> None:
        self.cookies_path = cookies_path
        self.feed = feed
        self.tweet_limit = max(5, int(tweet_limit))
        self.scroll_delay = max(0.25, float(scroll_delay))
        self.scroll_attempts = max(1, int(scroll_attempts))
        self.cache_ttl = max(60.0, float(cache_ttl))
        self._cache: Dict[Tuple[str, str, int], Dict[str, object]] = {}
        self._lock = threading.Lock()

    def _cache_key(self, query: str, limit: Optional[int], feed: Optional[str]) -> Tuple[str, str, int]:
        normalized_query = query.strip()
        normalized_feed = (feed or self.feed).lower() or DEF_FEED
        effective_limit = int(limit or self.tweet_limit)
        return (normalized_query, normalized_feed, effective_limit)

    def fetch(
        self,
        query: str,
        *,
        limit: Optional[int] = None,
        feed: Optional[str] = None,
    ) -> List[Dict[str, Optional[Any]]]:
        """Return cached posts for ``query`` (refreshing when the cache expired)."""

        key = self._cache_key(query, limit, feed)
        now = time.time()
        with self._lock:
            cached = self._cache.get(key)
            if cached and now - float(cached.get("ts", 0.0)) < self.cache_ttl:
                return cached.get("posts", [])  # type: ignore[return-value]

        posts = fetch_top_posts(
            query,
            feed=feed or self.feed,
            tweet_limit=int(limit or self.tweet_limit),
            scroll_delay=self.scroll_delay,
            scroll_attempts=self.scroll_attempts,
            cookies_path=self.cookies_path,
        )

        with self._lock:
            self._cache[key] = {"ts": now, "posts": posts}
        return posts


async def _run_cli_async(args: argparse.Namespace) -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    queries = [q.strip() for q in args.query.split(",") if q.strip()]
    if not queries:
        log.error("Keine gültigen Suchbegriffe angegeben.")
        return

    data = await scrape_queries_async(
        queries,
        feed=args.feed,
        tweet_limit=args.tweet_limit,
        scroll_delay=args.scroll_delay,
        scroll_attempts=args.scroll_attempts,
        cookies_path=args.cookies,
        html_dump=args.html_dump or None,
    )

    if len(queries) == 1 and not args.rich_json:
        # Maintain backwards compatibility with the legacy script output format.
        posts = data.get(queries[0], [])
        payload: Union[List[str], Dict[str, List[Dict[str, Optional[Any]]]]] = [
            str(p.get("text"))
            for p in posts
            if isinstance(p, dict) and p.get("text")
        ]
    else:
        payload = data

    Path(args.out).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    log.info("💾 Exportiert nach %s", args.out)


def main() -> None:
    args = parse_args()
    _ensure_playwright_available()
    asyncio.run(_run_cli_async(args))


if __name__ == "__main__":
    main()
