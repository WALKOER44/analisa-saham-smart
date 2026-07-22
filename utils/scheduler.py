from datetime import datetime
from app import run_analysis

LIVE_START = 9
LIVE_END = 16

def is_market_hours():
    now = datetime.now()
    return LIVE_START <= now.hour < LIVE_END

def run_loop(interval_minutes=15):
    print(f"[SCHEDULER] Mode LIVE ({LIVE_START}:00-{LIVE_END}:00 WIB)")
    print(f"[SCHEDULER] Interval: {interval_minutes} menit")
    print("[SCHEDULER] Notifier berjalan real-time di background (60 detik)")
    while True:
        if is_market_hours():
            print(f"[SCHEDULER] LIVE - menjalankan analisis...")
            run_analysis()
        else:
            print(f"[SCHEDULER] FINAL - 1x run lalu selesai")
            run_analysis()
            break
        import time
        time.sleep(interval_minutes * 60)
