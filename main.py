import os

from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from config import LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET
from request_context import set_base_url
from routers import image_router, travel, yt_router

os.makedirs("media", exist_ok=True)

app = FastAPI()
app.mount("/media", StaticFiles(directory="media"), name="media")

handler = WebhookHandler(LINE_CHANNEL_SECRET)
configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)

_text_handlers = [
    travel.register(configuration),
    yt_router.register(configuration),
    image_router.register(configuration),
]


@handler.add(MessageEvent, message=TextMessageContent)
def handle_text(event: MessageEvent):
    for text_handler in _text_handlers:
        text_handler(event)


@app.post("/callback")
async def callback(request: Request):
    signature = request.headers.get("X-Line-Signature", "")
    body = await request.body()
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("host", request.url.netloc)
    set_base_url(f"{scheme}://{host}")
    try:
        handler.handle(body.decode(), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    return "OK"
