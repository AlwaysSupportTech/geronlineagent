import json
import os
import time

from linebot.v3.messaging import (
    ApiClient,
    FlexBubble,
    FlexBox,
    FlexButton,
    FlexCarousel,
    FlexImage,
    FlexMessage,
    FlexText,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    URIAction,
)
from linebot.v3.webhooks import MessageEvent

from services.youtube import search_videos_by_topic

TRIGGER_KEYWORDS = {"推薦影片", "熱門影片", "YouTube", "youtube"}
_RECOMMEND_REASON = "健康、理財、人際溝通、房地產相關影片"

_CACHE_PATH = "yt_recommend_cache.json"
_CACHE_TTL_SECONDS = 12 * 60 * 60


def _read_cache() -> list[dict] | None:
    try:
        if time.time() - os.path.getmtime(_CACHE_PATH) > _CACHE_TTL_SECONDS:
            return None
        with open(_CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _write_cache(videos: list[dict]) -> None:
    with open(_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(videos, f, ensure_ascii=False)


def _format_views(views: str) -> str:
    n = int(views)
    if n >= 10000:
        return f"{n // 10000}萬次觀看"
    return f"{n:,}次觀看"


def _build_bubble(video: dict, reason: str) -> FlexBubble:
    return FlexBubble(
        hero=FlexImage(
            url=video["thumbnail"],
            size="full",
            aspect_ratio="20:13",
            aspect_mode="cover",
        ),
        body=FlexBox(
            layout="vertical",
            spacing="sm",
            contents=[
                FlexText(text=video["title"], weight="bold", wrap=True, size="sm"),
                FlexText(text=video["channel"], size="xs", color="#888888"),
                FlexText(text=_format_views(video["views"]), size="xs", color="#aaaaaa"),
                FlexText(text=reason, size="xs", color="#3B82F6", wrap=True),
            ],
        ),
        footer=FlexBox(
            layout="vertical",
            contents=[
                FlexButton(
                    action=URIAction(label="立即觀看", uri=f"https://youtu.be/{video['videoId']}"),
                    style="primary",
                    color="#FF0000",
                )
            ],
        ),
    )


def register(configuration):
    def handle_text(event: MessageEvent):
        if event.message.text.strip() not in TRIGGER_KEYWORDS:
            return
        merged = _read_cache()
        if not merged:
            videos = search_videos_by_topic()
            merged = [{**v, "reason": _RECOMMEND_REASON} for v in videos]
            _write_cache(merged)
        bubbles = [_build_bubble(v, v["reason"]) for v in merged]
        if bubbles:
            message = FlexMessage(
                alt_text="台灣 YouTube 熱門影片推薦",
                contents=FlexCarousel(contents=bubbles),
            )
        else:
            message = TextMessage(text="這次熱門影片中沒有找到跟健康/理財/人際溝通/房地產相關的影片，晚點再試試看吧！")
        with ApiClient(configuration) as client:
            MessagingApi(client).reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[message],
                )
            )

    return handle_text
