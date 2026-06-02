from __future__ import annotations

import math
import re
from typing import Any


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in parts if len(s.strip()) > 20]


def _tokens(sentence: str) -> list[str]:
    return re.findall(r"\b\w+\b", sentence.lower())


def _tf(tokens: list[str]) -> dict[str, float]:
    freq: dict[str, int] = {}
    for t in tokens:
        freq[t] = freq.get(t, 0) + 1
    total = len(tokens) or 1
    return {w: c / total for w, c in freq.items()}


def _idf(sentences: list[list[str]]) -> dict[str, float]:
    n = len(sentences)
    doc_freq: dict[str, int] = {}
    for toks in sentences:
        for w in set(toks):
            doc_freq[w] = doc_freq.get(w, 0) + 1
    return {w: math.log(n / df) for w, df in doc_freq.items()}


def extract_key_points(
    text: str = "",
    max_points: int = 5,
    lang: str = "auto",
) -> dict[str, Any]:
    if not text or not text.strip():
        return {"tool": "summarize", "key_points": [], "word_count": 0, "truncated": False}

    # Limit input to 20k chars to avoid huge payloads
    truncated = len(text) > 20_000
    text = text[:20_000] if truncated else text

    sents = _sentences(text)
    if not sents:
        return {"tool": "summarize", "key_points": [text.strip()], "word_count": len(text.split()), "truncated": truncated}

    tokenized = [_tokens(s) for s in sents]
    idf = _idf(tokenized)

    scores: list[tuple[float, int]] = []
    for i, toks in enumerate(tokenized):
        tf = _tf(toks)
        score = sum(tf[w] * idf.get(w, 0) for w in tf)
        # Slight position boost for first and last sentences
        if i == 0 or i == len(sents) - 1:
            score *= 1.2
        scores.append((score, i))

    top = sorted(scores, key=lambda x: -x[0])[:max_points]
    top_indices = sorted(idx for _, idx in top)
    key_points = [sents[i] for i in top_indices]

    return {
        "tool": "summarize",
        "key_points": key_points,
        "word_count": len(text.split()),
        "truncated": truncated,
    }
