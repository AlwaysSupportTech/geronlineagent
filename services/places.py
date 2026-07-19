import re

import requests

from config import PLACE_API_KEY

_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
_FIELD_MASK = "places.rating,places.regularOpeningHours.weekdayDescriptions"
_FALLBACK_HOURS = ["營業時間請洽現場"] * 7


def _clean_hours_line(desc: str) -> str:
    parts = re.split(r"[:：]", desc, maxsplit=1)
    return parts[-1].strip() if len(parts) > 1 else desc.strip()


def get_place_info(name: str, region: str) -> dict:
    try:
        response = requests.post(
            _SEARCH_URL,
            json={"textQuery": f"{region} {name}", "languageCode": "zh-TW"},
            headers={
                "X-Goog-Api-Key": PLACE_API_KEY,
                "X-Goog-FieldMask": _FIELD_MASK,
                "Content-Type": "application/json",
            },
            timeout=10,
        )
        response.raise_for_status()
        places = response.json().get("places") or []
    except requests.RequestException as e:
        print("[Places] request failed:", e)
        return {"rating": None, "openingHours": _FALLBACK_HOURS}

    if not places:
        return {"rating": None, "openingHours": _FALLBACK_HOURS}

    place = places[0]
    rating = place.get("rating")
    weekday_descriptions = (place.get("regularOpeningHours") or {}).get("weekdayDescriptions")
    if weekday_descriptions and len(weekday_descriptions) == 7:
        opening_hours = [_clean_hours_line(d) for d in weekday_descriptions]
    else:
        opening_hours = _FALLBACK_HOURS

    return {"rating": rating, "openingHours": opening_hours}
