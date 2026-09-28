# Phiếu Phản Ánh — K4 Level 3A, Ngày 12

> **Bài làm cá nhân.** Trả lời bằng lời của chính bạn, dựa trên những gì bạn
> quan sát được khi chạy code — không sao chép đáp án của người khác.
>
> Cách trả lời: thay dòng `> *Câu trả lời của bạn*` bằng câu trả lời.
> `grade.py` đếm số câu đã trả lời (15 điểm cho 10 câu).
>
> Họ và tên: Trần Thị Thúy — Mã học viên: 2A202602960
> Bản giải thích tham khảo kèm bằng chứng do trợ lý chạy; học viên cần đọc, kiểm chứng và diễn đạt lại theo hiểu biết của mình. Các thí nghiệm Docker/cloud chưa thực hiện được ghi rõ.

---

### Câu 1 — Fail fast (CP1)

Trong `Settings`, `agent_api_key` không có giá trị mặc định nên app chết ngay
khi khởi động nếu thiếu biến môi trường. Hãy mô tả một tình huống cụ thể mà
việc "chết sớm" này cứu bạn, so với việc để mặc định `"changeme"`.

Khi deploy bản mới mà quên đặt AGENT_API_KEY trong dashboard, Settings báo lỗi ngay lúc startup nên không nhận traffic với khóa mặc định mà người khác có thể đoán. Nếu để changeme, deploy trông như thành công nhưng bất kỳ ai biết khóa mẫu đều gọi được API. Lifespan gọi get_settings() để validation thực sự chạy lúc khởi động.

---

### Câu 2 — Log cho máy đọc (CP1)

Chạy service và gọi `/ask` vài lần. Dán một dòng log JSON bạn thu được, rồi
nêu **hai** việc bạn làm được với dòng log đó mà `print("đã trả lời xong")`
không làm được.

Log thực tế từ scripts/smoke_local.py (ASGI TestClient + FakeRedis):

```json
{"user_id": "smoke-user", "tokens_in": 3, "tokens_out": 37, "cost_usd": 2.265e-05, "event": "ask_completed", "level": "info", "timestamp": "2026-09-28T07:34:17.710854+00:00"}
```

Có thể lọc theo user_id để cộng chi phí theo người dùng; có thể tổng hợp tokens_in/tokens_out và số ask_completed theo thời gian để theo dõi mức sử dụng. Log chỉ ghi “đã trả lời xong” không có các trường này.

---

### Câu 3 — Kích thước image (CP2)

Build cả hai phiên bản và ghi lại số đo thật:

```bash
docker build -f Dockerfile.single -t agent:single .
docker build -t agent:multi .
docker images | grep agent
```

| Bản | Dung lượng |
|-----|-----------|
| 1 stage (bản đầu) | Chưa đo — chưa có Docker |
| Multi-stage | Chưa đo — chưa có Docker |

Giải thích: phần dung lượng chênh lệch đó là những gì?

> *Câu trả lời của bạn*

---

### Câu 4 — Thứ tự lệnh trong Dockerfile (CP2)

Sửa một ký tự trong `app/main.py` rồi build lại. Với Dockerfile của bạn, những
layer nào được dùng lại từ cache, layer nào phải chạy lại? Nếu bạn đặt
`COPY . .` lên trước `RUN pip install` thì kết quả khác thế nào?

Theo thứ tự Dockerfile hiện tại: sửa app/main.py chỉ làm mất cache từ COPY app và các bước phụ thuộc phía sau; COPY requirements.txt, tạo venv và pip install ở builder được tái sử dụng nếu requirements/base không đổi. Đặt COPY . . trước pip install khiến sửa source cũng làm bước cài thư viện chạy lại. Đây là phân tích Dockerfile; chưa xác minh cache bằng build thật vì máy chưa có Docker.

> *Câu trả lời của bạn*

---

### Câu 5 — Vì sao không chạy bằng root (CP2)

Container mặc định chạy bằng root. Mô tả chuỗi sự kiện dẫn từ "một lỗ hổng
trong code Python của bạn" tới "kẻ tấn công có quyền cao trên máy host", và
lệnh `USER` cắt đứt chuỗi đó ở chỗ nào.

Lỗ hổng Python có thể cho phép thực thi lệnh trong container với quyền của process. Nếu process là root, kẻ tấn công có nhiều quyền hơn để sửa file, khai thác mount nhạy cảm hoặc lỗ hổng kernel/runtime để vượt ranh giới container. Root trong container không tự động đồng nghĩa root trên host; còn phụ thuộc namespace, capability, mount và lỗ hổng. USER agent giảm quyền ngay tại bước thực thi lệnh trong container, nhưng không thay thế các lớp cô lập khác.

---

### Câu 6 — Cửa sổ trượt (CP3)

Rate limit của bạn dùng sliding window 60 giây. Nếu thay bằng cách đếm theo
phút đồng hồ (reset lúc giây 00), một người dùng có thể gửi tối đa bao nhiêu
request trong 2 giây liên tiếp khi hạn mức là 10/phút? Giải thích cách đạt được
con số đó.

Tối đa 20 request: gửi 10 ngay trước ranh giới phút, rồi 10 ngay sau khi bộ đếm reset. Sliding window xét liên tục 60 giây gần nhất nên 10 request đầu vẫn được tính khi nhóm sau đến.

---

### Câu 7 — Rate limit và cost guard (CP3)

Hai cơ chế này khác nhau ở điểm nào? Cho một tình huống mà rate limit cho qua
nhưng cost guard phải chặn, và một tình huống ngược lại.

Rate limit giới hạn số lượt trên một khoảng thời gian; cost guard giới hạn chi phí tích lũy theo tháng. User mới gửi một request trong phút nhưng đã tiêu hơn 10 USD trong tháng sẽ qua rate limit và bị cost guard chặn 402. User còn 9 USD nhưng gửi request thứ 11 trong 60 giây sẽ bị rate limit chặn 429. Bản lab check rồi record nên một lượt đang xử lý có thể làm vượt ngân sách; cần reservation chi phí nếu muốn giới hạn cứng khi chạy LLM thật hoặc nhiều request đồng thời.

---

### Câu 8 — /health khác /ready (CP4)

Nếu gộp hai endpoint làm một và cho nó kiểm tra Redis, chuyện gì xảy ra với cụm
3 container khi Redis mất kết nối 30 giây? Trả lời theo đúng thứ tự sự kiện.

Redis mất kết nối → endpoint gộp bắt đầu báo lỗi → nếu orchestrator dùng endpoint đó làm liveness và số lỗi vượt ngưỡng, cả 3 container bị restart → restart không sửa được Redis nên có thể tiếp tục lỗi/restart → khi Redis phục hồi, cụm vẫn phải chờ khởi động và vượt probe. Với hai endpoint riêng, /health vẫn 200, /ready báo 503 để rút traffic. Việc có restart trong 30 giây hay không còn phụ thuộc chu kỳ probe và failure threshold.

---

### Câu 9 — Stateless (CP4)

Chạy `docker compose up --scale agent=3` rồi gọi `/ask` nhiều lần với cùng một
`X-User-Id`. Quan sát `history_length` trong response. Nếu lịch sử được lưu
trong một dict Python thay vì Redis, bạn sẽ thấy con số đó thay đổi thế nào?

Smoke test ASGI + FakeRedis ghi nhận history_length: 0, 2, 4, 6, 8, 10, 12, 14, 16, 18. Test CP4 cũng kiểm tra hai đối tượng store dùng cùng Redis nhìn thấy cùng history. Đây chưa phải thí nghiệm 3 container. Nếu dùng dict riêng, các request qua A/B/C sẽ thấy các chuỗi lịch sử riêng, ví dụ 0, 0, 0, 2, 2, 2; số đếm có thể giảm khi chuyển sang instance ít history hơn. Đã thêm docker-compose.scale.yml để tránh trùng cổng khi chạy thí nghiệm thật.

> *Câu trả lời của bạn*

---

### Câu 10 — Deploy thật (CP5)

Ghi lại **một** lỗi bạn gặp khi deploy lên cloud (build fail, health check
timeout, sai REDIS_URL, app không đọc `$PORT`...): thông báo lỗi là gì, bạn
tìm ra nguyên nhân bằng cách nào, và sửa ra sao?

> *Câu trả lời của bạn*
