import time
import threading
from datetime import datetime
from .config import Config


class Scheduler:
    def __init__(self, config: Config, run_once=None):
        self.config   = config
        self.run_once = run_once
        self.interval = config.get("schedule.interval_minutes", 60) * 60
        self.running  = False
        self._thread  = None

    def start(self):
        self.running = True
        print(f"  Scheduler started — running every {self.interval // 60} minutes")
        print(f"  Press Ctrl+C to stop\n")

        if self.config.get("schedule.run_on_start", True):
            self._execute()

        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n  Scheduler stopped.")
            self.running = False

    def _loop(self):
        while self.running:
            time.sleep(self.interval)
            if self.running:
                self._execute()

    def _execute(self):
        print(f"  [{datetime.now().strftime('%H:%M:%S')}] Running scrape cycle...")
        try:
            self.run_once()
        except Exception as e:
            print(f"  Scheduler error: {e}")
