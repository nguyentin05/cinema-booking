#!/bin/bash

echo "🚀 Đang khởi động hệ thống Cinema Booking..."

echo "🌐 Bật Flask Web Server..."
python run.py &
FLASK_PID=$!

sleep 2

echo "⚙️ Bật Celery Worker..."
python -m celery -A celery_worker.celery_app worker --pool=solo --loglevel=info &
CELERY_PID=$!

cleanup() {
    echo -e "\n🛑 Đang tắt toàn bộ hệ thống một cách an toàn..."
    kill $FLASK_PID $CELERY_PID 2>/dev/null

    wait $FLASK_PID $CELERY_PID 2>/dev/null

    echo "✅ Đã tắt xong!"
    exit 0
}

# Dùng lệnh trap để gọi hàm cleanup khi nhấn Ctrl+C (SIGINT) hoặc bị kill (SIGTERM)
trap cleanup SIGINT SIGTERM

# Lệnh wait ở cuối để script không bị thoát ra ngay lập tức mà đứng đợi Flask và Celery chạy
wait