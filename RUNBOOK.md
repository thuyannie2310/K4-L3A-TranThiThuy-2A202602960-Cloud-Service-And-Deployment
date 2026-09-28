# Chạy và kiểm chứng bài lab

Học viên: Trần Thị Thúy — 2A202602960 (theo tên repository).

## Kết quả cuối ngày 2026-09-28

- Chạy `grade.py --no-bonus` trong container trên máy Windows: **100.0/100** phần bắt buộc. Output: `artifacts/grade-windows.txt`.
- CP5: 9 passed, 4 skipped; đã kiểm tra cloud bằng API key thật, không dùng LOCAL_FALLBACK.
- CP2 bỏ qua 2 test cần Docker CLI bên trong container; build image và chạy stack Docker thật đã được quan sát riêng trên host Windows.
- Railway: /health và /ready trả 200; /ask có key trả 200, thiếu key trả 401; rate limit trả 10 lượt 200 rồi 5 lượt 429.
- Docker local: 3 agent healthy cùng Redis và nginx; lịch sử 0,2,4,6,8.
- Đây là điểm tự chấm; câu trả lời và bằng chứng vẫn do giảng viên đánh giá.

## Kiểm chứng trước đó trên máy macOS

- CP1–CP4: 68 passed, 2 skipped (thiếu Docker).
- Kiểm tra bổ sung: 4 passed, bao gồm request đồng thời, ranh giới 60 giây, hết ngân sách và fail-fast lúc startup.
- ASGI smoke test + FakeRedis: health/ready 200, thiếu key 401, vượt budget 402, 10 lượt thành công rồi 5 lượt 429; history 0,2,…,18.
- Bằng chứng ở `artifacts/`. Đây chưa phải bằng chứng Docker hoặc cloud.

## Chạy lại offline

```bash
source .venv/bin/activate
python -m pytest tests/test_cp1.py tests/test_cp2.py tests/test_cp3.py tests/test_cp4.py tests/test_regressions.py -v
python scripts/smoke_local.py
```

## Chạy stack thật khi có Docker

Tạo `.env` từ `.env.example`, sinh khóa bằng `python -c "import secrets; print(secrets.token_urlsafe(32))"`, lưu vào `AGENT_API_KEY`. Không đưa khóa vào Git.

```bash
docker build -f Dockerfile.single -t agent:single .
docker build -t agent:multi .
docker images agent
docker compose up -d --build
curl -i http://localhost:8000/health
curl -i http://localhost:8000/ready
```

Ghi dung lượng thật vào câu 3; sửa một comment trong app/main.py rồi build lại để quan sát cache cho câu 4.

## Thử 3 instance

```bash
docker compose -f docker-compose.yml -f docker-compose.scale.yml up -d --build --scale agent=3
```

Nginx giữ cổng 8000; các agent chỉ dùng cổng nội bộ. Override cần Compose 2.24.4+ ([tài liệu Docker](https://docs.docker.com/reference/compose-file/merge/)). Gọi /ask cùng X-User-Id và lưu kết quả cho câu 9. Lịch sử tối đa 20 message.

## Hoàn tất hồ sơ nộp bài

- Đã điền đủ 10 câu trong exercises.md từ code và quan sát thực tế.
- Đã điền URL, cấu hình, kết quả và lỗi triển khai trong DEPLOYMENT.md.
- Còn bổ sung ảnh dashboard Railway và /health cloud vào screenshots/.
- Kiểm tra tên repo theo mẫu có DAY12 và CloudServicesAndDeployment, MSSV, rồi nộp liên kết repo lên Codelab.
- Bonus CI/CD chưa thực hiện; lần chấm dùng --no-bonus.

## Giới hạn của thiết kế lab

- X-User-Id do client gửi, không phải danh tính đã được xác minh riêng; không phù hợp để phân quyền/billing thật chỉ bằng header này.
- Cost guard kiểm tra tổng đã chi rồi ghi nhận sau lượt gọi; không reserve ngân sách cho request đang chạy.
- FakeRedis chỉ phục vụ kiểm thử/local, không dùng để scale nhiều process hoặc deploy cloud.
