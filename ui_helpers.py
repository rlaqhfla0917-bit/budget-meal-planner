"""Presentation and browser-history utilities for bowlly.

No recipe instructions are fabricated: links open an external recipe search.
History payloads contain only the current browser user's selections.
"""
import json
from datetime import datetime
from urllib.parse import quote
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
HISTORY_KEY = "bowlly_meal_history_v1"
ROLES = (("밥", "name1"), ("국·찌개", "name2"), ("주메뉴", "name3"), ("반찬", "name4"))


def meal_parts(meal):
    """Convert actual four-dish optimizer output into a labelled set meal."""
    return [{"role": role, "name": str(meal.get(key, "")).strip()}
            for role, key in ROLES if str(meal.get(key, "")).strip()]


def recipe_search_url(dish):
    """Search rather than claim a verified first-party recipe exists."""
    return "https://www.google.com/search?q=" + quote(f"{dish} 만드는 법 레시피")


def read_history(value):
    """Parse browser storage defensively; never load shared server-side history."""
    if value is None:
        return []
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (ValueError, TypeError):
            return []
    if isinstance(value, dict):
        value = value.get("items", [])
    if not isinstance(value, list):
        return []
    result = []
    seen = set()
    for item in value:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            continue
        if item["id"] in seen:
            continue
        if not isinstance(item.get("meals"), list) or not isinstance(item.get("shopping"), list):
            continue
        seen.add(item["id"])
        result.append(item)
    return sorted(result, key=lambda x: x.get("id", ""), reverse=True)[:30]


def merge_history(existing, incoming):
    """Keep local fresh changes if the browser component returns a stale snapshot."""
    merged = {r["id"]: r for r in read_history(incoming)}
    merged.update({r["id"]: r for r in read_history(existing)})
    return read_history(list(merged.values()))


def create_record(result, budget, household, meal_count, now=None):
    now = now or datetime.now(KST)
    selected = []
    for r in result["selected"]:
        selected.append({
            "name1": str(r.get("name1", "")),
            "name2": str(r.get("name2", "")),
            "name3": str(r.get("name3", "")),
            "name4": str(r.get("name4", "")),
            "kcal": round(float(r.get("kcal", 0)), 1),
            "protein_g": round(float(r.get("protein_g", 0)), 1),
            "sodium_mg": round(float(r.get("sodium_mg", 0)), 1),
        })
    shopping = json.loads(result["shopping"].to_json(orient="records", force_ascii=False))
    return {
        "id": now.strftime("%Y%m%d%H%M%S%f"),
        "created_at": now.strftime("%Y.%m.%d %H:%M"),
        "budget": int(budget),
        "household": int(household),
        "meal_count": int(meal_count),
        "total_cost": round(float(result["total_cost"])),
        "within_budget": bool(result["within_budget"]),
        "candidate_count": int(result.get("candidate_count", 0)),
        "meals": selected,
        "shopping": shopping,
        "status": "planned",
        "purchased_at": None,
    }


def mark_purchased(record, now=None):
    now = now or datetime.now(KST)
    changed = dict(record)
    changed["status"] = "purchased"
    changed["purchased_at"] = now.strftime("%Y.%m.%d %H:%M")
    return changed


def history_json(history):
    return json.dumps(read_history(history), ensure_ascii=False, allow_nan=False)
