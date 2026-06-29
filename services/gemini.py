import json
import google.generativeai as genai
from config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)
for m in genai.list_models():
    print(m.name, "->", m.supported_generation_methods)

_model = genai.GenerativeModel("gemini-3-flash-preview")

_PROMPT = """請給我「{region}」最值得去的 5 個景點，用 JSON array 回傳，不要加任何說明文字。
格式：[{{"name": "景點名", "description": "30字以內描述", "tip": "一句小提示"}}]"""


def get_attractions(region: str) -> list[dict]:
    response = _model.generate_content(_PROMPT.format(region=region))
    text = response.text.strip()
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    return json.loads(text)
