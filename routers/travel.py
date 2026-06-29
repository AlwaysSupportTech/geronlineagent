from urllib.parse import quote

from linebot.v3.messaging import (
    ApiClient,
    FlexBubble,
    FlexBox,
    FlexButton,
    FlexCarousel,
    FlexMessage,
    FlexText,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    URIAction,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from services.gemini import get_attractions

user_state: dict[str, str] = {}


def _build_bubble(attraction: dict) -> FlexBubble:
    name = attraction["name"]
    maps_url = f"https://www.google.com/maps/search/{quote(name)}"
    return FlexBubble(
        header=FlexBox(
            layout="vertical",
            background_color="#1E3A5F",
            padding_all="lg",
            contents=[
                FlexText(
                    text=name,
                    color="#FFFFFF",
                    weight="bold",
                    size="lg",
                    wrap=True,
                )
            ],
        ),
        body=FlexBox(
            layout="vertical",
            spacing="md",
            contents=[
                FlexText(
                    text=attraction["description"],
                    wrap=True,
                    size="sm",
                ),
                FlexText(
                    text=f"💡 {attraction['tip']}",
                    wrap=True,
                    size="xs",
                    color="#888888",
                ),
            ],
        ),
        footer=FlexBox(
            layout="vertical",
            contents=[
                FlexButton(
                    action=URIAction(label="查看地圖", uri=maps_url),
                    style="primary",
                    color="#1E3A5F",
                )
            ],
        ),
    )


TRIGGER_KEYWORDS = {"出去玩", "旅遊", "景點"}


def register(handler, configuration):
    @handler.add(MessageEvent, message=TextMessageContent)
    def handle_text(event: MessageEvent):
        user_id = event.source.user_id
        text = event.message.text.strip()

        if text in TRIGGER_KEYWORDS:
            user_state[user_id] = "waiting_for_region"
            with ApiClient(configuration) as client:
                MessagingApi(client).reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text="想去哪裡呢？輸入地區名稱吧！")],
                    )
                )
            return

        if user_state.get(user_id) != "waiting_for_region":
            return
        del user_state[user_id]
        region = text
        attractions = get_attractions(region)
        bubbles = [_build_bubble(a) for a in attractions]
        with ApiClient(configuration) as client:
            MessagingApi(client).reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        FlexMessage(
                            alt_text=f"{region} 景點推薦",
                            contents=FlexCarousel(contents=bubbles),
                        )
                    ],
                )
            )
