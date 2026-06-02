from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Any

import requests

from tools._shared import TIMEOUT, err

ARXIV_API_URL = "https://export.arxiv.org/api/query"
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}


def _clean_id(arxiv_id: str) -> str:
    match = re.search(r"(\d{4}\.\d{4,5}(?:v\d+)?)", arxiv_id or "")
    return match.group(1) if match else arxiv_id.strip()


def _fetch_metadata(arxiv_id: str) -> dict[str, Any]:
    resp = requests.get(
        ARXIV_API_URL,
        params={"id_list": arxiv_id, "max_results": 1},
        headers={"User-Agent": "AI20k-Day04-Research-Agent/1.0"},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    root = ET.fromstring(resp.text)
    entry = root.find(".//atom:entry", NS)
    if entry is None:
        raise ValueError(f"No entry found for arxiv_id={arxiv_id}")

    def text(path: str) -> str:
        node = entry.find(path, NS)
        return (node.text or "").strip() if node is not None else ""

    authors = [
        (a.find("atom:name", NS).text or "").strip()
        for a in entry.findall("atom:author", NS)
        if a.find("atom:name", NS) is not None
    ]
    published = text("atom:published")[:10]  # YYYY-MM-DD
    year = published[:4] if published else "n.d."

    return {
        "arxiv_id": arxiv_id,
        "title": " ".join(text("atom:title").split()),
        "authors": authors,
        "year": year,
        "published": published,
        "url": f"https://arxiv.org/abs/{arxiv_id}",
    }


def _bibtex(m: dict[str, Any]) -> str:
    first_author_last = (m["authors"][0].split()[-1] if m["authors"] else "Unknown")
    key = f"{first_author_last}{m['year']}{m['title'].split()[0].lower()}"
    author_field = " and ".join(m["authors"]) if m["authors"] else "Unknown"
    return (
        f"@article{{{key},\n"
        f"  title   = {{{m['title']}}},\n"
        f"  author  = {{{author_field}}},\n"
        f"  year    = {{{m['year']}}},\n"
        f"  journal = {{arXiv preprint arXiv:{m['arxiv_id']}}},\n"
        f"  url     = {{{m['url']}}}\n"
        f"}}"
    )


def _apa(m: dict[str, Any]) -> str:
    if not m["authors"]:
        author_str = "Unknown"
    elif len(m["authors"]) == 1:
        parts = m["authors"][0].split()
        author_str = f"{parts[-1]}, {'. '.join(p[0] for p in parts[:-1])}."
    elif len(m["authors"]) <= 6:
        formatted = []
        for a in m["authors"]:
            parts = a.split()
            formatted.append(f"{parts[-1]}, {'. '.join(p[0] for p in parts[:-1])}.")
        author_str = ", ".join(formatted[:-1]) + f", & {formatted[-1]}"
    else:
        parts = m["authors"][0].split()
        author_str = f"{parts[-1]}, {'. '.join(p[0] for p in parts[:-1])}., et al."
    return f"{author_str} ({m['year']}). {m['title']}. arXiv:{m['arxiv_id']}. {m['url']}"


def _plain(m: dict[str, Any]) -> str:
    authors = ", ".join(m["authors"][:3])
    if len(m["authors"]) > 3:
        authors += " et al."
    return f"{authors} ({m['year']}). \"{m['title']}\". arXiv:{m['arxiv_id']}"


def format_citation(arxiv_id: str = "", style: str = "bibtex") -> dict[str, Any]:
    try:
        clean_id = _clean_id(arxiv_id)
        if not clean_id:
            raise ValueError("arxiv_id is required")

        meta = _fetch_metadata(clean_id)
        style = (style or "bibtex").lower().strip()

        if style == "apa":
            citation = _apa(meta)
        elif style in ("plain", "text"):
            citation = _plain(meta)
        else:
            citation = _bibtex(meta)
            style = "bibtex"

        return {
            "tool": "cite",
            "arxiv_id": clean_id,
            "style": style,
            "citation": citation,
            "title": meta["title"],
            "authors": meta["authors"],
            "year": meta["year"],
        }
    except Exception as exc:
        return err("cite", exc)
