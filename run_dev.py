import subprocess
import sys
import time


def main():
    print("🚀 Đang khởi động hệ thống Cinema Booking...")
    print("🌐 Bật Flask Web Server...")
    flask_process = subprocess.Popen([sys.executable, "run.py"])

    time.sleep(2)

    print("⚙️ Bật Celery Worker...")
    celery_process = subprocess.Popen(
        [sys.executable, "-m", "celery", "-A", "celery_worker.celery_app", "worker", "--pool=solo", "--loglevel=info"]
    )

    try:
        flask_process.wait()
        celery_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Đang tắt toàn bộ hệ thống một cách an toàn...")
        flask_process.terminate()
        celery_process.terminate()
        flask_process.wait()
        celery_process.wait()
        print("✅ Đã tắt xong!")


if __name__ == "__main__":
    main()
