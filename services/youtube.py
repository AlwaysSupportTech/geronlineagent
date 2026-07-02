import random
from googleapiclient.discovery import build
from config import GOOGLE_API_KEY

# TODO: 看看 response 裡面有沒有 category => 健康、理財、人際溝通、房地產、網劇爛片
def get_trending(region: str = "TW", fetch: int = 30, sample: int = 10) -> list[dict]:
    youtube = build("youtube", "v3", developerKey=GOOGLE_API_KEY)
    response = youtube.videos().list(
        part="snippet,statistics",
        chart="mostPopular",
        regionCode=region,
        maxResults=fetch,
    ).execute()
    print("[YouTube response]", [item["snippet"]["title"] for item in response["items"]])
    items = random.sample(response["items"], min(sample, len(response["items"])))
    return [
        {
            "videoId": item["id"],
            "title": item["snippet"]["title"],
            "channel": item["snippet"]["channelTitle"],
            "views": item["statistics"].get("viewCount", "0"),
            "thumbnail": item["snippet"]["thumbnails"]["high"]["url"],
        }
        for item in items
    ]
