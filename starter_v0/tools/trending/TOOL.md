---
name: trending
track: core
kind: api_read
requires_env: [RAPIDAPI_KEY, RAPIDAPI_TWITTER_HOST]
inputs: [country, limit]
outputs: [items, country]
side_effect: false
---
# trending

Lấy danh sách trending topics trên Twitter/X theo quốc gia. Dùng khi user muốn biết chủ đề đang hot mà không có keyword cụ thể. Khác với social_search (cần keyword), trending trả về những gì đang được thảo luận nhiều nhất hiện tại.
