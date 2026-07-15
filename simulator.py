from __future__ import annotations

import math
import random
import threading
import time
from datetime import timedelta

from db import insert_event, make_event, process_incremental, utc_now


class LiveRingSimulator:
    def __init__(self, interval_seconds: float = 2.0):
        self.interval_seconds = interval_seconds
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.counter = 0
        self.steps_today = 8400
        self.last_hr_record_id: str | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, daemon=True, name="ring-simulator")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _run(self) -> None:
        random.seed()
        last_pipeline = 0.0
        while not self._stop.is_set():
            self.counter += 1
            now = utc_now()
            circadian = 6 * math.sin((now.hour - 8) / 24 * 2 * math.pi)
            hr = max(48, min(150, random.gauss(72 + circadian + random.choice([0,0,0,4,10]), 3.5)))
            event = make_event("heart_rate", now, hr, "bpm")
            self.last_hr_record_id = event["record_id"]
            insert_event(event)

            self.steps_today += random.randint(4, 28)
            insert_event(make_event("steps", now, self.steps_today, "count"))

            if self.counter % 4 == 0:
                insert_event(make_event("blood_oxygen", now, max(92, min(100, random.gauss(97.1, .7))), "percent"))
                insert_event(make_event("skin_temperature", now, max(32.5, min(36, random.gauss(33.7, .25))), "celsius"))
            if self.counter % 8 == 0:
                insert_event(make_event("energy_score", now, max(40, min(98, random.gauss(82, 4))), "score"))

            # A late correction proves that the same business key is updated, not duplicated.
            if self.counter % 12 == 0 and self.last_hr_record_id:
                correction = make_event(
                    "heart_rate", now - timedelta(minutes=4), hr + 2, "bpm",
                    record_id=self.last_hr_record_id, modified_delay=300,
                )
                insert_event(correction)

            # A source deletion proves delete propagation.
            if self.counter % 20 == 0 and self.last_hr_record_id:
                delete = make_event(
                    "heart_rate", now - timedelta(minutes=2), None, "bpm",
                    record_id=self.last_hr_record_id, operation="DELETE", modified_delay=420,
                )
                insert_event(delete)

            if time.time() - last_pipeline >= 5:
                process_incremental()
                last_pipeline = time.time()
            self._stop.wait(self.interval_seconds)
