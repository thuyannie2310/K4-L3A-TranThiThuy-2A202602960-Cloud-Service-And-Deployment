# Thông tin deploy — Checkpoint 5

## Thông tin học viên

- Họ và tên: Trần Thị Thúy
- Mã học viên: 2A202602960
- Repo: https://github.com/thuyannie2310/K4-L3A-TranThiThuy-2A202602960-Cloud-Service-And-Deployment

## Service

- Public URL: https://k4-l3a-tranthithuy-2a202602960-cloud-service-and-production.up.railway.app
- Platform: Railway
- Ngày deploy: 2026-09-28
- Project: supportive-tranquility
- Build: Dockerfile; cổng HTTP: 8080; healthcheck: /health.
- App và Redis hiển thị Online trên dashboard.

## Cấu hình môi trường

| Biến | Nguồn |
|---|---|
| AGENT_API_KEY | Học viên nhập riêng trong Railway Variables; không ghi giá trị vào repo |
| REDIS_URL | Tham chiếu biến REDIS_URL của service Redis trong cùng project |
| PORT | Railway tự cấp, quan sát thấy 8080 |
| RATE_LIMIT_PER_MINUTE | Mặc định của Settings: 10 |
| MONTHLY_BUDGET_USD | Mặc định của Settings: 10.0 |
| LOG_LEVEL | Mặc định của Settings: INFO |

## Kết quả kiểm tra HTTP thực tế

Kiểm tra từ máy trợ lý bằng httpx, xác minh TLS bật mặc định:

```text
GET /health → 200
{"status":"ok","service":"day12-agent","version":"1.0.0"}

GET /ready → 200
{"status":"ready","redis":true}

POST /ask, body {"question":"Hello"}, không gửi API key → 401
{"detail":"invalid or missing API key"}
```

Kiểm tra từ container Docker trên máy Windows, gửi API key bằng header (không in khóa):

```text
POST /ask với key thật, user cloud-check → 200
history_length: 0; cost_usd: 0.00002505; tokens: in=3, out=41
Response có answer hợp lệ.

15 request với cùng user mới →
[200, 200, 200, 200, 200, 200, 200, 200, 200, 200, 429, 429, 429, 429, 429]
```

Output rate limit gốc trên Windows: `artifacts/cloud-rate-limit-windows.txt`; bản văn bản tương ứng: `artifacts/cloud-rate-limit.txt`.

Chạy `grade.py --no-bonus` trong container Windows: 100.0/100 phần bắt buộc; riêng CP5: 9 passed, 4 skipped. API key cloud được lấy từ môi trường, không in vào output. Kết quả: `artifacts/grade-windows.txt`.

## Lỗi đã xử lý

Lần khởi động đầu, Deploy Logs báo `ValidationError: 1 validation error for Settings`, `agent_api_key`, `Field required`, rồi `Application startup failed. Exiting.` App thiếu AGENT_API_KEY vì .env local không được đưa lên cloud. Đã đặt khóa trong Railway Variables, thêm tham chiếu Redis và deploy lại. App khởi động thành công, /health và /ready trả 200.

Khi kết nối GitHub ban đầu, Railway App bị yêu cầu cài vào tổ chức lớp không có quyền quản trị. Đã chọn tài khoản cá nhân thuyannie2310 và chỉ cấp quyền repo bài lab.

## Ảnh minh chứng

- [screenshots/dashboard.png](screenshots/dashboard.png): đã chụp lại ngày 2026-09-28, app và Redis đều Online.
- Ảnh `/health` cloud còn thiếu: lần chụp lại ngày 2026-09-28, Chrome báo `ERR_BLOCKED_BY_CLIENT` cả sau khi tải lại. Đây là lỗi truy cập phía trình duyệt; kết quả HTTP kiểm tra trước đó được ghi ở trên.
- screenshots/scale-history.png: đã lưu thí nghiệm Docker local 3 agent.

Không dùng LOCAL_FALLBACK cho bản deploy này.
