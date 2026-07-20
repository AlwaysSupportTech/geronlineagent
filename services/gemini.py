import json
import re
from google import genai
from google.genai import types
from config import GEMINI_API_KEY

client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options=types.HttpOptions(
        timeout=90000,
        retry_options=types.HttpRetryOptions(attempts=2),
    ),
)

# for m in client.models.list():
#     print(m.name, "->", m.supported_actions)

_model = "gemini-3.1-flash-lite"
_search_model = "gemini-3.1-flash-lite"
_image_model = "gemini-3.1-flash-image"  # 目前的合理預設值，若模型名稱失效請依錯誤訊息調整

_PROMPT = """請推薦「{region}」最適合電視新聞或旅遊節目介紹的 5 個景點。

挑選原則：
- 具代表性、話題性或視覺特色，適合電視畫面呈現
- 優先選擇近期熱門、季節活動、文化特色、自然奇景或具地方故事的景點
- 避免過於冷門、資訊不足或一般性商場
- 不要聲稱景點曾被特定新聞或節目報導，除非可明確確認

僅回傳合法 JSON array，不要加任何說明、Markdown 或程式碼區塊。

格式：
[
  {{
    "name": "景點名",
    "description": "30字以內、適合新聞或節目介紹的亮點",
    "tip": "一句指出遊客到現場最值得特別關注的畫面、細節或體驗"
  }}
]"""

_FILTER_PROMPT = """以下是 YouTube 台灣熱門影片清單（JSON），請從中挑選最多 5 支
與「健康、理財、人際溝通、房地產」這些主題最相關的影片。
避免：內容與這些主題無關、標題黨、純廣告內容。
只回傳 JSON array，不要加任何說明文字。
格式：[{{"videoId": "...", "reason": "一句中文推薦理由"}}]

影片清單：
{videos_json}"""

_SEARCH_PROMPT = """請搜尋目前 YouTube 上與「健康、理財、人際溝通、房地產」這些主題相關、
較熱門或近期發布的影片，挑出最多 5 支與主題高度相關的影片。
避免：內容與這些主題無關、標題黨、純廣告內容。
只回傳 JSON array，不要加任何說明文字，也不要用 markdown 包住。
每個物件請包含以下欄位：
- videoId: YouTube 影片 ID（11 碼）
- title: 影片標題
- channel: 頻道名稱
- views: 觀看次數，純數字字串（例如 "125000"），若無法取得精確數字請給合理估計整數，不要用「萬」「千」等單位
- reason: 一句中文推薦理由
格式：[{{"videoId": "...", "title": "...", "channel": "...", "views": "...", "reason": "..."}}]"""


_REQUEST_OPTIONS = {"timeout": 90}


def _parse_json(text: str) -> list:
    text = text.strip()
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    text = re.sub(r",(\s*[}\]])", r"\1", text)
    return json.loads(text)


def get_attractions(region: str) -> list[dict]:
    response = client.models.generate_content(
        model=_model,
        contents=_PROMPT.format(region=region),
    )
    print("[Gemini get_attractions]", response.text)
    return _parse_json(response.text)


def generate_image(prompt: str) -> bytes:
    response = client.models.generate_content(
        model=_image_model,
        contents=prompt,
        config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
    )
    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            return part.inline_data.data
    raise RuntimeError("Gemini 沒有回傳圖片資料")


def filter_videos(videos: list[dict]) -> list[dict]:
    slim = [{"videoId": v["videoId"], "title": v["title"]} for v in videos]
    response = client.models.generate_content(
        model=_model,
        contents=_FILTER_PROMPT.format(videos_json=json.dumps(slim, ensure_ascii=False)),
    )
    print("[Gemini filter_videos]", response.text)
    return _parse_json(response.text)


def search_topic_videos(count: int = 5) -> list[dict]:
    """用 Gemini + Google 搜尋直接找出主題相關影片並整理成 LINE 卡片所需格式，
    取代「先抓大量 trending 再用 Gemini 篩選、再查 YouTube API 補資料」的三段流程。"""
    total = client.models.count_tokens(
        model=_search_model,
        contents=_SEARCH_PROMPT
    )
    print(f"[SEARCH Input Token]: {total.total_tokens}")
    
    response = client.models.generate_content(
        model=_search_model,
        contents=_SEARCH_PROMPT,
        # config=config
    )
    usage = response.usage_metadata
    print(f"[SEARCH Input Token]: {usage.candidates_token_count}")
    print("[Gemini search_topic_videos]", response.text)
    videos = _parse_json(response.text)[:count]
    for video in videos:
        video["thumbnail"] = f"https://i.ytimg.com/vi/{video['videoId']}/hqdefault.jpg"
    return videos
