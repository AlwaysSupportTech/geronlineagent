import json
import google.generativeai as genai
from config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)
for m in genai.list_models():
    print(m.name, "->", m.supported_generation_methods)

_model = genai.GenerativeModel("gemini-3-flash-preview")

_PROMPT = """請給我「{region}」最值得去的 5 個景點，用 JSON array 回傳，不要加任何說明文字。
格式：[{{"name": "景點名", "description": "30字以內描述", "tip": "一句小提示"}}]"""

_FILTER_PROMPT = """以下是 YouTube 台灣熱門影片清單（JSON），請從中挑選 5 支最值得推薦的影片。
避免：重複相似主題、標題黨、低品質或純廣告內容。
只回傳 JSON array，不要加任何說明文字。
格式：[{{"videoId": "...", "reason": "一句中文推薦理由"}}]

影片清單：
{videos_json}"""


_REQUEST_OPTIONS = {"timeout": 90}


def _parse_json(text: str) -> list:
    text = text.strip()
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    return json.loads(text)


def get_attractions(region: str) -> list[dict]:
    response = _model.generate_content(_PROMPT.format(region=region), request_options=_REQUEST_OPTIONS)
    print("[Gemini get_attractions]", response.text)
    return _parse_json(response.text)


def filter_videos(videos: list[dict]) -> list[dict]:
    slim = [{"videoId": v["videoId"], "title": v["title"], "channel": v["channel"]} for v in videos]
    response = _model.generate_content(
        _FILTER_PROMPT.format(videos_json=json.dumps(slim, ensure_ascii=False)),
        request_options=_REQUEST_OPTIONS,
    )
    print("[Gemini filter_videos]", response.text)
    return _parse_json(response.text)
