import random
from googleapiclient.discovery import build
from config import GOOGLE_API_KEY

# 19 旅行與活動, 22 人物與網誌, 25 新聞與政治, 27 教育, 28 科學與技術
CATEGORY_IDS = {"19", "22", "25", "27", "28"}


def _format_item(item: dict) -> dict:
    return {
        "videoId": item["id"],
        "title": item["snippet"]["title"],
        "channel": item["snippet"]["channelTitle"],
        "views": item["statistics"].get("viewCount", "0"),
        "thumbnail": item["snippet"]["thumbnails"]["high"]["url"],
    }


def get_videos_by_ids(video_ids: list[str]) -> list[dict]:
    """直接用 videoId 查詢影片詳細資料，用於 Gemini 搜尋結果的資料補齊。"""
    if not video_ids:
        return []
    youtube = build("youtube", "v3", developerKey=GOOGLE_API_KEY)
    response = youtube.videos().list(
        part="snippet,statistics",
        id=",".join(video_ids),
    ).execute()
    return [_format_item(item) for item in response.get("items", [])]


_TOPIC_QUERY = "健康 理財 人際溝通 房地產"


def search_videos_by_topic(count: int = 5, region: str = "TW") -> list[dict]:
    """用 YouTube Data API 的 search().list 直接搜尋主題相關影片並回傳前 count 筆，
    資料保證是真實存在的影片，不像 Gemini 生成可能會有不存在的 videoId。"""
    youtube = build("youtube", "v3", developerKey=GOOGLE_API_KEY)
    search_response = youtube.search().list(
        part="id",
        q=_TOPIC_QUERY,
        type="video",
        regionCode=region,
        relevanceLanguage="zh-Hant",
        order="relevance",
        maxResults=count,
    ).execute()
    video_ids = [item["id"]["videoId"] for item in search_response.get("items", [])]
    return get_videos_by_ids(video_ids)


# TODO: 看看 response 裡面有沒有 category => 健-網劇爛片
def get_trending(region: str = "TW", fetch: int = 300, sample: int = 300) -> list[dict]:
    youtube = build("youtube", "v3", developerKey=GOOGLE_API_KEY)
    raw_items = []
    page_token = None
    while len(raw_items) < fetch:
        response = youtube.videos().list(
            part="snippet,statistics",
            chart="mostPopular",
            regionCode=region,
            maxResults=50,
            pageToken=page_token,
        ).execute()
        raw_items.extend(response["items"])
        page_token = response.get("nextPageToken")
        print(page_token)
        if not page_token:
            break
    with open("300ytlist.txt", "w", encoding="utf-8") as f:
        f.write(f"[Youtube Raw Items] {raw_items}")
    items = [
        item
        for item in raw_items
        if item["snippet"].get("categoryId") in CATEGORY_IDS
    ]
    print("[YouTube response]", [item["snippet"]["title"] for item in items])
    items = random.sample(items, min(sample, len(items)))
    return [_format_item(item) for item in items]
