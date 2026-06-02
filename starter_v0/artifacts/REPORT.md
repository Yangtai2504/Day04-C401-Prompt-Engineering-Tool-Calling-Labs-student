# Day 04 Lab v2 Report — Research Agent

## Team

- **Team:** Team 3 — Zone 12
- **Members:**
  - Nguyễn Thái Dương — 2A202600823
  - Đỗ Trung Kiên — 2A202600711
  - Trần Lương — 2A202600881
- **Provider/model:** OpenRouter / openai/gpt-4o-mini

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research agent: tìm tweet theo tài khoản/từ khóa, tìm tin tức web, đọc URL, tìm/trích dẫn paper arXiv, tổng hợp kết quả thành digest markdown, và gửi lên Telegram sau khi xác nhận.

**Link dùng thử:** chạy local `streamlit run app.py` và expose qua ngrok.

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|----------|------------|---------------------|
| clarify | Hỏi lại user khi thiếu info hoặc cần confirm trước khi gửi | Không |
| timeline | Lấy tweet mới nhất của 1 tài khoản Twitter | Không |
| social_search | Tìm tweet theo từ khóa (Latest / Top) | Không |
| lookup | Tìm tin tức / thông tin web (Tavily) | Không |
| fetch | Đọc nội dung một URL cụ thể (Firecrawl) | Không |
| format | Format kết quả thành markdown digest | Không |
| send | Gửi text lên Telegram (chỉ khi confirmed=true) | Không |
| policy | Tìm trong company policy nội bộ | Không |
| papers | Tìm paper trên arXiv | Không |
| paper_text | Tải và đọc PDF arXiv | Không |
| **cite** | Format citation BibTeX/APA/plain từ arxiv_id | **Có** |
| summarize | Trích key points từ văn bản dài (TF-IDF) | Có |
| trending | Lấy trending topics hôm nay (Tavily news) | Có |

## A3. Câu hỏi mẫu để thử

1. `Tweet mới nhất của Andrej Karpathy là gì?`
2. `Tin tức AI nổi bật hôm nay có gì?`
3. `Tìm trên web tin AI hôm nay và tìm thêm tweet về AI.`
4. `Cho tôi BibTeX citation của bài arXiv 1706.03762`
5. `Tìm 5 bài báo mới nhất về AI agents trên arXiv` → rồi `Lấy citation APA của bài đầu tiên`
6. `Tìm cả web lẫn tweet về Anthropic đi`

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---------|-----------------|------------|:---:|:---:|---------|
| v0 | baseline | — | — | 0.70 | runs/v0_B_base_openrouter_20260602T123929686422.json |
| v1 | system_prompt.md | Instruction "đừng hỏi, tự đoán" là nguyên nhân agent không gọi `clarify` (R10, R11) và không từ chối out-of-scope (R08, R14) | 0.70 | 0.80 | runs/v1_B_base_openrouter_20260602T125555898789.json |
| v2 | system_prompt.md | `clarify` rules chưa đủ mạnh (R10, R11 vẫn fail); `send` contradiction — prompt vừa bảo confirm lại vừa bảo "gửi luôn" (R12 fail) | 0.80 | 0.85 | runs/v2_B_base_openrouter_20260602T140500497716.json |
| v3 | system_prompt.md + tools.yaml | (a) Prompt hardcode 5 handle → học vẹt, R01 regression; (b) confirm rule áp nhầm lên `fetch` → R04 fail; (c) agent hỏi content thay vì yes_no cho `send` → R12 fail | 0.85 | **1.00** | runs/v3_B_base_openrouter_20260602T142456510324.json |

## B2. Failure Analysis

Dựa trên `results[*].result.failures` từ `runs/v0_B_base_openrouter_20260602T123929686422.json`.

| Case ID | Failure Type | Actual Tool Calls (v0) | What Failed | Fix (version) |
|---------|-------------|----------------------|-------------|--------------|
| R08_out_of_scope | out_of_scope | `lookup("nguyên hàm x^2")` | Agent gọi tool cho câu toán ngoài phạm vi | v1: thêm scope section vào prompt |
| R10_missing_handle | missing_info | `timeline("sama")` (tự đoán) | Agent tự đoán handle "sama" thay vì hỏi clarify | v1: xóa "đừng hỏi, tự đoán" |
| R11_missing_url | missing_info | `fetch("https://openai.com")` (bịa URL) | Agent tự bịa URL thay vì hỏi link | v2: rule clarify cho "bài này/link này" |
| R12_confirm_before_send | wrong_boundary | `send(confirmed=true)` trực tiếp | Gửi Telegram không qua clarify yes_no | v3: enforce "clarify yes_no TRƯỚC send" + tools.yaml |
| R13_parallel_web_and_tweets | wrong_tool | `lookup(...)` only | Chỉ gọi 1 tool, bỏ sót `social_search` | v2: side effect của việc làm rõ scope |
| R14_out_of_scope_coding | out_of_scope | `lookup("hàm Fibonacci Python")` | Agent tìm web cho câu coding | v1: scope boundary |

## B3. Team Eval Cases

10 cases trong `data/eval_group.json` — kết quả **10/10 PASS** sau khi fix 2 case sai logic.

| Case ID | What It Tests | Expected Tool | Result |
|---------|--------------|--------------|--------|
| G01_trending_routing | "trending gì" không keyword → `trending`, không phải `social_search` | `trending()` | ✅ PASS |
| G02_cite_bibtex_direct | arxiv_id rõ + yêu cầu BibTeX → `cite` trực tiếp | `cite(1706.03762, bibtex)` | ✅ PASS |
| G03_cite_missing_id | "bài báo này" không ID → `clarify` hỏi ID | `clarify(text)` | ✅ PASS |
| G04_no_tool_greeting | Lời cảm ơn → không gọi tool | no_tool | ✅ PASS |
| G05_cite_apa_style | Yêu cầu APA → style=apa, không dùng default bibtex | `cite(2501.05729, apa)` | ✅ PASS |
| MG01_papers_then_cite | 3 turns: tìm paper → user cung cấp arxiv_id → xác nhận BibTeX | `cite(1706.03762, bibtex)` | ✅ PASS |
| MG02_trending_then_search | 3 turns: trending → tweet về topic → top tweets | `social_search(AI, Top)` | ✅ PASS |
| MG03_clarify_then_cite | 3 turns: thiếu ID → user cho ID → xác nhận APA | `cite(2301.08243, apa)` | ✅ PASS |
| MG04_correction_cite_style | 3 turns: cite → đổi sang APA → xác nhận giữ bài | `cite(1706.03762, apa)` | ✅ PASS |
| MG05_web_and_twitter | 3 turns: news → add twitter → cả hai nguồn | `lookup` + `social_search(Anthropic)` | ✅ PASS |

## B4. Live Chat Evidence

File: `transcripts/live_v3_openrouter_20260602T160851867391.transcript.json`

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|------|-------------|-----------|-----------------|---------|
| 1 | "Tìm tin tức nổi bật về AI hôm nay" | `lookup(AI, news, day)` | Routing đúng topic=news, timeframe=day | ✅ PASS |
| 2 | "Tóm tắt bài viết này hộ tôi" (không có URL) | `clarify(text)` | Thiếu URL → hỏi lại trước (v1 fix) | ✅ PASS |
| 3 | "https://openai.com/research/" | `fetch(url)` | Có URL → fetch ngay, không hỏi thêm | ✅ PASS |
| 4 | "Chỉ đọc đúng link đó thôi nhé" | `fetch(url)` | Carry URL từ lượt trước, không bịa URL mới | ✅ PASS |
| 5 | "Đăng bản tin AI hôm nay lên Telegram giúp tôi" | `clarify(yes_no)` | Confirm trước khi send (v3 fix) | ✅ PASS |
| 6 | "Có, xác nhận gửi đi nhé" | `send(confirmed=true)` | Send sau confirm — fail vì thiếu TELEGRAM_BOT_TOKEN (expected) | ✅ PASS |

## B5. Bonus Evidence

| Bonus | Evidence | What Worked | Risk / Guardrail |
|-------|---------|-------------|-----------------|
| send (Telegram) | Turn 5-6 transcript; R12 PASS | Agent luôn gọi `clarify(yes_no)` trước `send`. Không bao giờ gửi trực tiếp | Thiếu TELEGRAM_BOT_TOKEN → fail gracefully với thông báo rõ |
| arXiv / papers | MG01, MG03 PASS; G02, G05 PASS | `papers` → `paper_text` chain; `cite` tạo BibTeX/APA từ arxiv_id chính xác | arXiv rate-limit 3s/request; timeout 60s để tránh timeout từ VN |
| UI Streamlit | app.py | Provider selector, model selector, version picker (current/v1/v2/v3), tool call expanders, transcript autosave, ngrok tunnel share | Max tokens slider (default 2048) để tránh 402 credit error OpenRouter |
| Tool mới (3 tools) | tools/cite/, tools/summarize/, tools/trending/ | `cite`: format BibTeX/APA/plain từ arXiv metadata — dùng được thực tế; `summarize`: TF-IDF extractive; `trending`: Tavily news search | `summarize` và `trending` overlap với existing tools — `cite` là tool thực sự có giá trị |

## B6. Reflection

**Fixes thuộc `system_prompt.md`:**
- Xóa "đừng hỏi, tự đoán" → fix R10, R11
- Thêm scope boundary → fix R08, R14
- Thêm "clarify yes_no TRƯỚC send" → fix R12
- Thêm routing rule: trending vs social_search, fetch không cần confirm
- Bỏ hardcode handle list → model tự dùng training knowledge

**Fixes thuộc `tools.yaml`:**
- `clarify` description: phân biệt `response_type=text` vs `yes_no`
- `send` description: enforce confirmed=true + clarify trước

**Failure cần manual review thay vì auto grading:**
- MG01 và MG05 ban đầu fail không phải vì agent sai mà vì eval case viết sai logic. Auto grader không phân biệt được. Phải đọc actual_tool_calls thủ công mới nhận ra.
- R12 "wrong_boundary": agent gọi `clarify(response_type=text)` thay vì `yes_no` — logic đúng (hỏi trước) nhưng sai kiểu hỏi. Auto grader mark FAIL nhưng behavior gần đúng.

**Cải thiện tiếp theo:**
- Thêm `TELEGRAM_BOT_TOKEN` để test end-to-end send thật
- Bỏ `summarize` (TF-IDF kém hơn LLM) và `trending` (= `lookup(news, day)`) khỏi tools.yaml để giảm routing confusion
- Tăng coverage cho `cite`: ID không hợp lệ, paper không tìm thấy, nhiều style
- Test với model khác (claude-3-5-haiku) để so sánh chaining behavior
