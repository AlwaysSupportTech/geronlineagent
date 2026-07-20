import random
from collections import Counter

from linebot.v3.messaging import (
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent

from services.youtube_scraper import search_youtube_links

TRIGGER_KEYWORDS = {"推薦影片", "熱門影片", "YouTube", "youtube"}

_TOPICS = ["健康", "理財", "人際溝通", "房地產"]
_LINK_COUNT = 5
_TOPIC_CAP = 2


def _pick_topics(n: int = _LINK_COUNT, cap: int = _TOPIC_CAP) -> list[str]:
    counts = {t: 0 for t in _TOPICS}
    picks = []
    for _ in range(n):
        candidates = [t for t in _TOPICS if counts[t] < cap]
        topic = random.choice(candidates)
        counts[topic] += 1
        picks.append(topic)
    return picks


def _collect_links(topics: list[str]) -> list[str]:
    links: list[str] = []
    seen = set()
    for topic, needed in Counter(topics).items():
        for link in search_youtube_links(f"{topic} 台灣", count=needed):
            if link not in seen:
                seen.add(link)
                links.append(link)
    random.shuffle(links)
    return links


def register(configuration):
    def handle_text(event: MessageEvent):
        if event.message.text.strip() not in TRIGGER_KEYWORDS:
            return

        topics = _pick_topics()
        print("[YT] topics:", topics)
        try:
            links = _collect_links(topics)
        except Exception as e:
            print("[YT] scrape failed:", e)
            links = None

        if links is None:
            messages = [TextMessage(text="爬取影片時發生錯誤，請稍後再試一次。")]
        elif links:
            messages = [TextMessage(text=link) for link in links]
        else:
            messages = [TextMessage(text="這次沒有找到相關影片，換個時間再試試看吧！")]

        with ApiClient(configuration) as client:
            MessagingApi(client).reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=messages,
                )
            )

    return handle_text
