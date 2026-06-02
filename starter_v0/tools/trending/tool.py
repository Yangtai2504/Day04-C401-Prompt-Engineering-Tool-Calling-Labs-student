from __future__ import annotations

import os
from typing import Any

import requests

from tools._shared import TIMEOUT, domain, err


def get_trending(country: str = "worldwide", limit: int = 10) -> dict[str, Any]:
    """
    Lấy trending topics hiện tại bằng cách kết hợp:
    - Tìm kiếm "trending topics today" trên Tavily (web + news)
    - Trả về danh sách chủ đề đang hot với link nguồn
    """
    try:
        key = os.getenv("TAVILY_API_KEY")
        if not key:
            raise RuntimeError("Missing TAVILY_API_KEY env var")

        location_hint = f"in {country}" if country.lower() not in ("worldwide", "global") else ""
        query = f"trending topics today {location_hint}".strip()

        response = requests.post(
            "https://api.tavily.com/search",
            json={
                "query": query,
                "topic": "news",
                "max_results": int(limit or 10),
                "search_depth": "basic",
                "time_range": "day",
            },
            headers={"Authorization": f"Bearer {key}"},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        items = []
        for item in data.get("results", []):
            items.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "source": domain(item.get("url", "")),
                "summary": item.get("content", ""),
                "score": item.get("score"),
            })

        return {
            "tool": "trending",
            "country": country,
            "query_used": query,
            "items": items,
        }
    except Exception as exc:
        return err("trending", exc)
