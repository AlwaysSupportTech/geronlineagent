from urllib.parse import quote

from linebot.v3.messaging import (
    ApiClient,
    FlexBubble,
    FlexBox,
    FlexButton,
    FlexCarousel,
    FlexIcon,
    FlexMessage,
    FlexSeparator,
    FlexText,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    URIAction,
)
from linebot.v3.webhooks import MessageEvent

from services.gemini import get_attractions
from services.places import get_place_info

user_state: dict[str, str] = {}

_GOLD_STAR_URL = "https://developers-resource.landpress.line.me/fx/img/review_gold_star_28.png"
_GRAY_STAR_URL = "https://developers-resource.landpress.line.me/fx/img/review_gray_star_28.png"
_WEEKDAY_LABELS = ["一", "二", "三", "四", "五", "六", "日"]


def _build_rating_row(rating) -> FlexBox | None:
    if not isinstance(rating, (int, float)):
        return None
    filled = round(rating)
    stars = [
        FlexIcon(size="sm", url=_GOLD_STAR_URL if i < filled else _GRAY_STAR_URL)
        for i in range(5)
    ]
    return FlexBox(
        layout="baseline",
        spacing="sm",
        contents=[
            *stars,
            FlexText(
                text=f"{rating:g}",
                size="sm",
                color="#888888",
                margin="md",
                flex=0,
            ),
        ],
    )


def _build_hours_box(opening_hours) -> FlexBox | None:
    if not isinstance(opening_hours, list) or len(opening_hours) != 7:
        return None
    return FlexBox(
        layout="vertical",
        spacing="xs",
        contents=[
            FlexBox(
                layout="baseline",
                spacing="sm",
                contents=[
                    FlexText(text=f"週{label}", size="xxs", color="#888888", flex=1),
                    FlexText(text=str(hours), size="xxs", color="#555555", flex=3),
                ],
            )
            for label, hours in zip(_WEEKDAY_LABELS, opening_hours)
        ],
    )


def _build_bubble(attraction: dict) -> FlexBubble:
    name = attraction["name"]
    maps_url = f"https://www.google.com/maps/search/{quote(name)}"

    body_contents = [
        FlexText(
            text=attraction["description"],
            wrap=True,
            size="sm",
        ),
    ]

    rating_row = _build_rating_row(attraction.get("rating"))
    if rating_row is not None:
        body_contents.append(rating_row)

    body_contents.append(
        FlexText(
            text=f"💡 {attraction['tip']}",
            wrap=True,
            size="xs",
            color="#888888",
        )
    )

    hours_box = _build_hours_box(attraction.get("openingHours"))
    if hours_box is not None:
        body_contents.append(FlexSeparator(margin="sm"))
        body_contents.append(
            FlexText(text="營業時間", size="xs", weight="bold", color="#80d9ff")
        )
        body_contents.append(hours_box)

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
            contents=body_contents,
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


def register(configuration):
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
            return True

        if user_state.get(user_id) != "waiting_for_region":
            return False
        del user_state[user_id]
        region = text
        attractions = get_attractions(region)
        for attraction in attractions:
            attraction.update(get_place_info(attraction["name"], region))
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
        return True

    return handle_text
