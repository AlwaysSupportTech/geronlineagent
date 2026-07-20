import os
import uuid

from linebot.v3.messaging import (
    ApiClient,
    ImageMessage,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent

from request_context import get_base_url
from services.gemini import generate_image

TRIGGER_KEYWORDS = {"生成圖片"}
_MEDIA_DIR = "media"

user_state: dict[str, str] = {}


def register(configuration):
    def handle_text(event: MessageEvent):
        user_id = event.source.user_id
        text = event.message.text.strip()

        if text in TRIGGER_KEYWORDS:
            user_state[user_id] = "waiting_for_prompt"
            with ApiClient(configuration) as client:
                MessagingApi(client).reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text="想生成什麼圖片呢？請輸入描述！")],
                    )
                )
            return True

        if user_state.get(user_id) != "waiting_for_prompt":
            return False
        del user_state[user_id]
        prompt = text

        with ApiClient(configuration) as client:
            api = MessagingApi(client)
            try:
                image_bytes = generate_image(prompt)
            except Exception as e:
                print("[ImageRouter] generate_image failed:", e)
                api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text="生成圖片時發生錯誤，請稍後再試一次。")],
                    )
                )
                return True

            os.makedirs(_MEDIA_DIR, exist_ok=True)
            filename = f"{uuid.uuid4().hex}.png"
            with open(os.path.join(_MEDIA_DIR, filename), "wb") as f:
                f.write(image_bytes)

            image_url = f"{get_base_url()}/media/{filename}"
            api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        ImageMessage(
                            original_content_url=image_url,
                            preview_image_url=image_url,
                        )
                    ],
                )
            )
        return True

    return handle_text
