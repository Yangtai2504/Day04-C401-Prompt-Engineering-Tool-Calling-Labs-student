# Demo Script — Team 3 Zone 12

**~2 phút | Provider: OpenRouter / gpt-4o-mini**

---

## Mở đầu (15s)

> *[Mở Streamlit UI]*

"Team 3 Zone 12 — mình build **Research Agent**: nhận yêu cầu → chọn tool → gọi tool thật → trả kết quả. Bài lab không đo chatbot trả lời hay, mà đo **vòng lặp evidence-driven**: chạy eval → đọc log → sửa → đo lại."

---

## Baseline v0 — vấn đề (20s)

> *[Show version_log.csv hoặc terminal output]*

"Chạy baseline được **70% (14/20)**. Đọc log thấy ngay: system_prompt bảo agent *'đừng hỏi, tự đoán, gửi luôn'* — intentional bug của bài. Kết quả: agent gọi tool cho câu toán, tự bịa URL, gửi Telegram không hỏi xác nhận."

---

## V1 → V2 → V3 (30s)

"3 vòng tối ưu, mỗi vòng **sửa 1 thứ**, đo trước/sau:

| Version | Thay đổi | Kết quả |
|---------|----------|---------|
| v1 | Xóa 'đừng hỏi, tự đoán' | 70% → **80%** |
| v2 | Thêm clarify rules + scope boundary | 80% → **85%** |
| v3 | Bỏ hardcode handle list + fix fetch/send rules | 85% → **100%** |

Điểm đáng chú ý ở v3: prompt cũ hardcode `Sam Altman → sama` — đó là **học vẹt**, chỉ đúng 5 người. Fix đúng là để model dùng training knowledge của nó."

---

## Demo live (30s)

> *[Gõ 3 câu trong UI]*

```
1. Tweet mới nhất của Andrej Karpathy?
   → timeline(karpathy)  ✓ map tên → handle tự động

2. Tóm tắt bài viết này hộ tôi
   → clarify(text)  ✓ thiếu URL → hỏi trước, không tự đoán

3. Đăng bản tin AI lên Telegram giúp tôi
   → clarify(yes_no)  ✓ confirm trước khi gửi
```

---

## Tool mới + Kết quả (25s)

"Mình thêm tool **`cite`** — format BibTeX/APA từ arxiv_id. Đây là gap thật: không tool nào làm được việc này. Workflow: `papers` → lấy ID → `cite` → paste vào LaTeX luôn.

**Group eval 10/10 PASS.** 2 case ban đầu fail không phải agent sai — là mình viết test sai. Evidence-driven review phân biệt được điều đó.

**Bài học**: prompt engineering là đặt đúng nguyên tắc, không phải học thuộc từng trường hợp."
