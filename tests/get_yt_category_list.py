from googleapiclient.discovery import build
import traceback

GOOGLE_API_KEY = ""  # Do not commit and input
GOOGLE_API_KEY = "AIzaSyAs2hc98uhSoajUmOp6J2lkW69W260RTSw"


youtube = build("youtube", "v3", developerKey=GOOGLE_API_KEY)

def get_youtube_categories():
    try:
        # 3. 執行 videoCategories.list 請求
        # part: 包含 snippet (名稱)
        # regionCode: 設定為台灣 (TW) 以取得該地區適用的分類
        # hl: 設定為 zh-Hant 以取得繁體中文名稱
        request = youtube.videoCategories().list(
            part="snippet",
            regionCode="TW",
            hl="zh-Hant"
        )
        response = request.execute()

        print(f"{'ID':<5} {'分類名稱':<20} {'可指派 (Assignable)':<20}")
        print("-" * 50)

        for item in response.get("items", []):
            cat_id = item["id"]
            title = item["snippet"]["title"]
            # assignable 代表一般使用者上傳影片時是否能選擇此分類
            assignable = item["snippet"].get("assignable", False)
            
            assignable_str = "是" if assignable else "否"
            
            print(f"{cat_id:<5} {title:<20} {assignable_str:<20}")

    except Exception as e:
        traceback.print_exc()



if __name__ == "__main__":
    get_youtube_categories()