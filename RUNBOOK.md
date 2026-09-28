# Chạy và kiểm chứng bài lab

Học viên: Trần Thị Thúy — 2A202602960 (theo tên repository).

## Đã kiểm chứng trên máy hiện tại

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

## Phần còn cần thực hiện

1. Chạy Docker build, đo image và kiểm tra scale thật.
2. Deploy bằng cấu hình Railway hoặc Render trong repo với Redis thật; cấu hình đã có nhưng chưa được kiểm chứng trên tài khoản cloud.
3. Điền Public URL, output thực tế, platform trong DEPLOYMENT.md; chụp dashboard và /health.
4. Hoàn thiện câu 3, 4, 9, 10 từ quan sát thực tế; đọc và diễn đạt lại các câu giải thích theo hiểu biết cá nhân.
5. Đổi tên repo GitHub đúng mẫu có DAY12 và CloudServicesAndDeployment; kiểm tra lại MSSV.
6. Chạy `python grade.py --no-bonus`, commit/push rồi nộp repo public lên Codelab.

Chưa cấu hình bonus CI/CD vì CP5 chưa hoàn thành. Không đặt LOCAL_FALLBACK để giả lập đạt CP5 khi chưa có stack Docker thật.

## Giới hạn của thiết kế lab

- X-User-Id do client gửi, không phải danh tính đã được xác minh riêng; không phù hợp để phân quyền/billing thật chỉ bằng header này.
- Cost guard kiểm tra tổng đã chi rồi ghi nhận sau lượt gọi; không reserve ngân sách cho request đang chạy.
- FakeRedis chỉ phục vụ kiểm thử/local, không dùng để scale nhiều process hoặc deploy cloud.
