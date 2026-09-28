# Phiếu Phản Ánh — K4 Level 3A, Ngày 12

> **Bài làm cá nhân.** Trả lời bằng lời của chính bạn, dựa trên những gì bạn
> quan sát được khi chạy code — không sao chép đáp án của người khác.
>
> Nội dung được tổng hợp từ mã nguồn, kết quả kiểm thử và thí nghiệm thực tế.
> `grade.py` đếm số câu đã trả lời (15 điểm cho 10 câu).
>
> Họ và tên: Trần Thị Thúy — Mã học viên: 2A202602960
> Nội dung có trợ lý AI hỗ trợ tổng hợp. Log CP1 lấy từ smoke test do trợ lý chạy; số đo Docker, cache và scale lấy từ ảnh thí nghiệm học viên gửi trên máy Windows. Học viên cần đọc, kiểm chứng và giải thích được nội dung. Câu 10 dựa trên Deploy Logs Railway và kiểm tra HTTP sau khi sửa.

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
docker images agent
```

| Bản | Dung lượng |
|-----|-----------|
| 1 stage (bản đầu) | 1,73 GB (Disk usage) |
| Multi-stage | 309 MB (Disk usage) |

Giải thích: phần dung lượng chênh lệch đó là những gì?

Theo ảnh kết quả `docker images agent`, bản một stage chiếm 1,73 GB và bản multi-stage chiếm 309 MB ở cùng cột Disk usage, giảm khoảng 82%. Cột Content size tương ứng là 447 MB và 71,9 MB; không trộn hai loại số đo khi so sánh.

Bản mới dùng `python:3.11-slim` thay cho bản Python đầy đủ nên giảm các công cụ và thư viện hệ điều hành không cần cho runtime. Runtime chỉ nhận venv từ builder cùng thư mục app và utils; bản cũ dùng COPY . . và giữ cache pip mặc định. Vì base image, phạm vi sao chép và cách cài thư viện cùng thay đổi, không thể quy toàn bộ mức giảm cho multi-stage hoặc khẳng định riêng compiler chiếm bao nhiêu nếu chưa đo từng layer.

---

### Câu 4 — Thứ tự lệnh trong Dockerfile (CP2)

Sửa một ký tự trong `app/main.py` rồi build lại. Với Dockerfile của bạn, những
layer nào được dùng lại từ cache, layer nào phải chạy lại? Nếu bạn đặt
`COPY . .` lên trước `RUN pip install` thì kết quả khác thế nào?

Sau khi thêm comment vào `app/main.py`, lưu file và chạy lại `docker build --progress=plain -t agent:multi .`, log cho thấy:

- Các bước COPY requirements.txt, tạo venv, pip install, tạo user, WORKDIR và COPY venv từ builder đều có trạng thái CACHED.
- Bước COPY app có trạng thái DONE 0.0s; bước COPY utils phía sau cũng DONE 0.0s, rồi Docker xuất image thành công.

Như vậy, thay đổi source không làm cài lại thư viện. Nếu đặt COPY . . trước RUN pip install trong cùng stage, thay đổi source sẽ làm mất cache của COPY và bước cài thư viện phụ thuộc phía sau, nên pip install phải chạy lại. Tùy cache tải gói, không nhất thiết mọi gói đều phải tải lại từ mạng.

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

Đã chạy stack bằng hai file Compose để tránh ba agent cùng chiếm cổng host 8000:

```bash
docker compose -f docker-compose.yml -f docker-compose.scale.yml up -d --build --scale agent=3
```

Kết quả compose ps cho thấy 3 agent healthy, Redis healthy và Nginx đang chạy ở cổng 8000. Gửi liên tiếp 5 request qua Nginx với cùng một X-User-Id mới thu được:

```text
[(200, 0), (200, 2), (200, 4), (200, 6), (200, 8)]
```

Mỗi cặp là (HTTP status, history_length). History tăng 2 sau mỗi lượt vì lưu cả câu hỏi của user và câu trả lời của assistant; response báo số message trước lượt hiện tại. Ảnh minh chứng: [scale-history.png](screenshots/scale-history.png).

Redis là nơi lưu lịch sử dùng chung giữa các instance. Kết quả trên xác nhận chuỗi hội thoại liên tục qua Nginx trong stack 3 agent; response không có instance ID nên riêng ảnh này không chứng minh từng request đã vào container nào. Nếu thay Redis bằng dict riêng và request được phân phối sang các instance khác nhau, mỗi instance sẽ có lịch sử riêng: có thể thấy 0, 0, 0, 2, 2, 2 hoặc số đếm giảm khi đổi instance. Khi process restart, dict cũng mất dữ liệu.

---

### Câu 10 — Deploy thật (CP5)

Ghi lại **một** lỗi bạn gặp khi deploy lên cloud (build fail, health check
timeout, sai REDIS_URL, app không đọc `$PORT`...): thông báo lỗi là gì, bạn
tìm ra nguyên nhân bằng cách nào, và sửa ra sao?

Lần deploy đầu lên Railway, image build xong nhưng app chuyển sang Crashed. Trong Deploy Logs có thông báo:

```text
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
agent_api_key
Field required [type=missing, input_value={'port': '8080'}, input_type=dict]
ERROR: Application startup failed. Exiting.
```

Traceback đi qua lifespan → get_settings() → Settings(), cho thấy lỗi xảy ra khi đọc cấu hình lúc startup. Kiểm tra tab Variables thấy app chưa có AGENT_API_KEY. File .env trên máy local không được commit hay đưa vào image, nên Railway không tự có khóa đó.

Cách sửa: nhập AGENT_API_KEY trong Railway Variables, đặt REDIS_URL tham chiếu Redis trong cùng project, rồi deploy lại. Sau khi sửa, app và Redis đều Online; kiểm tra URL HTTPS công khai nhận /health 200, /ready 200 với redis=true, và /ask không có key trả 401. Đây là ví dụ fail-fast giúp phát hiện thiếu secret trước khi app nhận request.
