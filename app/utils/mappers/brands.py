import httpx
import asyncio
import json
from typing import Any
from pydantic import BaseModel


class ChildCategory(BaseModel):
    id: int
    name: str
    parent: str
    url: str
    brands: list[str]


async def fetch_brands(cat_id: int, name: str, client: httpx.AsyncClient) -> list[str]:
    url = f"https://api.zoommer.ge/v1/Content/filter?catId={cat_id}"
    try:
        resp = await client.get(url)
        resp.raise_for_status()
        specs = resp.json().get("specifications", [])
        brand_spec = next((s for s in specs if s.get("id") == 22 or s.get("name", "").lower() == "brand"), None)
        return [v["value"] for v in brand_spec["values"]] if brand_spec else []
    except Exception as e:
        print(f"[ERROR] {name}: {e}")
        return []


async def fetch_subcategories(client: httpx.AsyncClient) -> list[ChildCategory]:
    resp = await client.get("https://api.zoommer.ge/v1/Categories/all-categories")
    if resp.status_code != 200:
        return []

    cats = resp.json()
    pairs = [(cat["name"], sub) for cat in cats for sub in cat.get("childCategories", [])]
    brands_list = await asyncio.gather(*[fetch_brands(sub["id"], sub["name"], client) for _, sub in pairs])

    return [
        ChildCategory(id=sub["id"], name=sub["name"], parent=parent, url=sub["url"], brands=b)
        for (parent, sub), b in zip(pairs, brands_list)
        if b
    ]


def summarize(categories: list[ChildCategory]) -> list[dict[str, Any]]:
    grouped: dict[str, list[ChildCategory]] = {}
    for c in categories:
        grouped.setdefault(c.parent, []).append(c)

    results = []
    for parent, subs in grouped.items():
        if all(len(s.brands) == 1 for s in subs):
            brands = sorted({b for s in subs for b in s.brands})
            text = f"For {parent} we have {', '.join(brands)} brands."
            results.append({"category": parent, "brands": brands, "text": text})
        else:
            for s in subs:
                text = f"For {parent} {s.name} we have {', '.join(s.brands)} brands."
                results.append({"category": parent, "subcategory": s.name, "brands": s.brands, "text": text})
    return results


async def main():
    timeout = httpx.Timeout(30.0, connect=10.0)
    limits = httpx.Limits(max_keepalive_connections=20, max_connections=50)

    async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
        subs = await fetch_subcategories(client)
        summaries = summarize(subs)

    with open("brand_summary.json", "w", encoding="utf-8") as f:
        json.dump(summaries, f, indent=2, ensure_ascii=False)
    print("✅ brand_summary.json written.")


if __name__ == "__main__":
    asyncio.run(main())