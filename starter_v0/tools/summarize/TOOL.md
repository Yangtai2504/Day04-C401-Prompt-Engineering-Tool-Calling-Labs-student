---
name: summarize
track: core
kind: local_processor
requires_env: []
inputs: [text, max_points, lang]
outputs: [key_points, word_count, truncated]
side_effect: false
---
# summarize

Extracts key points from a block of text using extractive summarization (TF-IDF sentence scoring). No external API required.

Use after `fetch` or `paper_text` to condense long content before passing to `format`.
