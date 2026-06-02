---
name: cite
track: core
kind: local_formatter
requires_env: []
inputs: [arxiv_id, style]
outputs: [citation, style, arxiv_id]
side_effect: false
---
# cite

Format citation cho một bài báo arXiv theo style BibTeX, APA, hoặc plain text.
Dùng sau khi có arxiv_id từ tool `papers`. Không cần API ngoài — gọi arXiv metadata API.

Workflow: papers(query) → lấy arxiv_id → cite(arxiv_id) → citation sẵn sàng dùng.
