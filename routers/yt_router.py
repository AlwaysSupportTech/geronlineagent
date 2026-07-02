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
    URIAction,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from services.gemini import filter_videos
from services.youtube import get_trending

TRIGGER_KEYWORDS = {"推薦影片", "熱門影片", "YouTube", "youtube"}


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


def register(handler, configuration):
    @handler.add(MessageEvent, message=TextMessageContent)
    def handle_text(event: MessageEvent):
        if event.message.text.strip() not in TRIGGER_KEYWORDS:
            return
        videos = get_trending()
        selected = filter_videos(videos)
        video_map = {v["videoId"]: v for v in videos}
        bubbles = [
            _build_bubble(video_map[s["videoId"]], s["reason"])
            for s in selected
            if s["videoId"] in video_map
        ]
        with ApiClient(configuration) as client:
            MessagingApi(client).reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        FlexMessage(
                            alt_text="台灣 YouTube 熱門影片推薦",
                            contents=FlexCarousel(contents=bubbles),
                        )
                    ],
                )
            )
