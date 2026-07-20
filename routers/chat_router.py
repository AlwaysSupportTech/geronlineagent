from linebot.v3.messaging import (
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent

from services.gemini import chat_reply


def register(configuration):
    def handle_text(event: MessageEvent):
        text = event.message.text.strip()
        try:
            reply = chat_reply(text)
        except Exception as e:
            print("[ChatRouter] chat_reply failed:", e)
            reply = "現在有點忙不過來，晚點再聊聊吧！"

        with ApiClient(configuration) as client:
            MessagingApi(client).reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply)],
                )
            )
        return True

    return handle_text
