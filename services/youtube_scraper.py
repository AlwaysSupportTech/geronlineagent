import concurrent.futures
from urllib.parse import quote_plus

from playwright.sync_api import sync_playwright

_SEARCH_URL = "https://www.youtube.com/results?search_query={query}&gl=TW&hl=zh-TW"
_VIDEO_LINK_SELECTOR = "ytd-video-renderer a#video-title"


def _scrape(query: str, count: int) -> list[str]:
    url = _SEARCH_URL.format(query=quote_plus(query))
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_selector(_VIDEO_LINK_SELECTOR, timeout=15000)
            hrefs = page.eval_on_selector_all(
                _VIDEO_LINK_SELECTOR,
                "els => els.map(el => el.getAttribute('href'))",
            )
        finally:
            browser.close()

    video_ids = []
    for href in hrefs:
        if not href or "watch?v=" not in href:
            continue
        video_id = href.split("watch?v=")[1].split("&")[0]
        if video_id not in video_ids:
            video_ids.append(video_id)
        if len(video_ids) >= count:
            break

    return [f"https://www.youtube.com/watch?v={video_id}" for video_id in video_ids]


def search_youtube_links(query: str, count: int = 5) -> list[str]:
    """在獨立執行緒執行 Playwright sync API，避免呼叫端（例如 FastAPI 的
    async callback）所在的執行緒已有 asyncio event loop 在跑而被 Playwright 拒絕。
    爬取失敗時直接讓例外往外拋，由呼叫端決定要顯示什麼錯誤訊息。"""
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(_scrape, query, count).result()
