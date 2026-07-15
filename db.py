from __future__ import annotations

import math
import os
import random
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

DEFAULT_DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR = Path(os.getenv("DATA_DIR", str(DEFAULT_DATA_DIR))).expanduser()
DB_PATH = DATA_DIR / "galaxy_ring.db"
UTC = timezone.utc
_LOCK = threading.RLock()


def utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def iso(dt: datetime) -> str:
    return dt.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@contextmanager
def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def initialize_db(reset: bool = False) -> None:
    if reset and DB_PATH.exists():
        DB_PATH.unlink()
    with _LOCK, connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS bronze_events (
                event_id TEXT PRIMARY KEY,
                record_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                device_id TEXT NOT NULL,
                metric_type TEXT NOT NULL,
                event_time_utc TEXT NOT NULL,
                end_time_utc TEXT,
                numeric_value REAL,
                unit TEXT,
                sleep_stage TEXT,
                operation TEXT NOT NULL CHECK(operation IN ('UPSERT','DELETE')),
                source_last_modified_utc TEXT NOT NULL,
                ingestion_time_utc TEXT NOT NULL,
                schema_version INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS silver_metrics (
                record_id TEXT NOT NULL,
                metric_type TEXT NOT NULL,
                user_id TEXT NOT NULL,
                device_id TEXT NOT NULL,
                event_time_utc TEXT NOT NULL,
                end_time_utc TEXT,
                numeric_value REAL,
                unit TEXT,
                sleep_stage TEXT,
                source_last_modified_utc TEXT NOT NULL,
                ingestion_time_utc TEXT NOT NULL,
                PRIMARY KEY (record_id, metric_type)
            );

            CREATE TABLE IF NOT EXISTS gold_daily_health (
                health_date TEXT NOT NULL,
                user_id TEXT NOT NULL,
                steps INTEGER,
                avg_heart_rate REAL,
                min_heart_rate REAL,
                max_heart_rate REAL,
                avg_blood_oxygen REAL,
                avg_skin_temperature REAL,
                sleep_minutes REAL,
                deep_sleep_minutes REAL,
                light_sleep_minutes REAL,
                rem_sleep_minutes REAL,
                awake_sleep_minutes REAL,
                energy_score REAL,
                last_metric_event_utc TEXT,
                refreshed_utc TEXT,
                PRIMARY KEY (health_date, user_id)
            );

            CREATE TABLE IF NOT EXISTS pipeline_state (
                pipeline_name TEXT PRIMARY KEY,
                watermark_utc TEXT NOT NULL,
                updated_utc TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS pipeline_runs (
                run_id TEXT PRIMARY KEY,
                started_utc TEXT NOT NULL,
                completed_utc TEXT NOT NULL,
                status TEXT NOT NULL,
                input_rows INTEGER NOT NULL,
                deduplicated_rows INTEGER NOT NULL,
                upsert_rows INTEGER NOT NULL,
                delete_rows INTEGER NOT NULL,
                duration_ms INTEGER NOT NULL,
                watermark_utc TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS data_quality (
                check_id TEXT PRIMARY KEY,
                check_time_utc TEXT NOT NULL,
                check_name TEXT NOT NULL,
                status TEXT NOT NULL,
                failed_rows INTEGER NOT NULL,
                details TEXT
            );
            """
        )
        now = iso(utc_now())
        conn.execute(
            "INSERT OR IGNORE INTO pipeline_state VALUES (?, ?, ?)",
            ("bronze_to_silver", "1900-01-01T00:00:00Z", now),
        )


def insert_event(event: dict) -> None:
    columns = [
        "event_id", "record_id", "user_id", "device_id", "metric_type",
        "event_time_utc", "end_time_utc", "numeric_value", "unit",
        "sleep_stage", "operation", "source_last_modified_utc",
        "ingestion_time_utc", "schema_version",
    ]
    with _LOCK, connect() as conn:
        conn.execute(
            f"INSERT OR IGNORE INTO bronze_events ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})",
            [event.get(c) for c in columns],
        )


def make_event(metric_type: str, event_time: datetime, value: float | None, unit: str | None,
               *, record_id: str | None = None, operation: str = "UPSERT",
               end_time: datetime | None = None, sleep_stage: str | None = None,
               modified_delay: int = 15, ingestion_delay: int = 2) -> dict:
    modified = event_time + timedelta(seconds=modified_delay)
    ingested = max(utc_now(), modified + timedelta(seconds=ingestion_delay))
    return {
        "event_id": str(uuid.uuid4()),
        "record_id": record_id or str(uuid.uuid4()),
        "user_id": "usr_demo_001",
        "device_id": "ring_demo_001",
        "metric_type": metric_type,
        "event_time_utc": iso(event_time),
        "end_time_utc": iso(end_time) if end_time else None,
        "numeric_value": round(value, 2) if value is not None else None,
        "unit": unit,
        "sleep_stage": sleep_stage,
        "operation": operation,
        "source_last_modified_utc": iso(modified),
        "ingestion_time_utc": iso(ingested),
        "schema_version": 1,
    }


def seed_history(days: int = 14, seed: int = 42) -> None:
    with connect() as conn:
        if conn.execute("SELECT COUNT(*) FROM bronze_events").fetchone()[0] > 0:
            return
    random.seed(seed)
    today = utc_now().replace(hour=0, minute=0, second=0)
    batch = []
    for day_offset in range(days - 1, -1, -1):
        day = today - timedelta(days=day_offset)
        # 48 heart-rate samples.
        for i in range(48):
            ts = day + timedelta(minutes=30 * i)
            circadian = 7 * math.sin((ts.hour - 8) / 24 * 2 * math.pi)
            activity = random.choice([0, 0, 0, 3, 8, 16])
            hr = max(48, min(145, random.gauss(69 + circadian + activity, 4)))
            batch.append(make_event("heart_rate", ts, hr, "bpm"))
        # Sleep-linked samples.
        sleep_start = day - timedelta(hours=random.uniform(1.1, 2.0))
        sleep_minutes = int(max(320, min(520, random.gauss(435, 38))))
        sleep_end = sleep_start + timedelta(minutes=sleep_minutes)
        batch.append(make_event("sleep_session", sleep_start, sleep_minutes, "minutes", end_time=sleep_end))
        stages = [("DEEP", .20), ("LIGHT", .54), ("REM", .20), ("AWAKE", .06)]
        cursor = sleep_start
        for stage, ratio in stages:
            mins = int(sleep_minutes * ratio)
            end = cursor + timedelta(minutes=mins)
            batch.append(make_event("sleep_stage", cursor, mins, "minutes", end_time=end, sleep_stage=stage))
            cursor = end
        for i in range(14):
            ts = sleep_start + (sleep_end - sleep_start) * (i / 13)
            batch.append(make_event("blood_oxygen", ts, max(91, min(100, random.gauss(96.7, .8))), "percent"))
            batch.append(make_event("skin_temperature", ts, max(32.2, min(36, random.gauss(33.8, .35))), "celsius"))
        batch.append(make_event("steps", day + timedelta(hours=23, minutes=55), int(max(1500, min(18000, random.gauss(9200, 2600)))), "count"))
        batch.append(make_event("energy_score", day + timedelta(hours=8), int(max(35, min(98, random.gauss(78, 9)))), "score"))

    with _LOCK, connect() as conn:
        columns = [
            "event_id", "record_id", "user_id", "device_id", "metric_type",
            "event_time_utc", "end_time_utc", "numeric_value", "unit",
            "sleep_stage", "operation", "source_last_modified_utc",
            "ingestion_time_utc", "schema_version",
        ]
        conn.executemany(
            f"INSERT OR IGNORE INTO bronze_events ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})",
            [[e.get(c) for c in columns] for e in batch],
        )
    process_incremental(force_all=True)


def process_incremental(force_all: bool = False) -> dict:
    started = utc_now()
    perf_started = time.perf_counter()
    run_id = str(uuid.uuid4())
    with _LOCK, connect() as conn:
        state = conn.execute(
            "SELECT watermark_utc FROM pipeline_state WHERE pipeline_name='bronze_to_silver'"
        ).fetchone()
        watermark = state[0]
        # SQLite datetime handles ISO strings after replacing Z.
        if force_all:
            source = conn.execute("SELECT * FROM bronze_events ORDER BY ingestion_time_utc").fetchall()
        else:
            source = conn.execute(
                """
                SELECT * FROM bronze_events
                WHERE datetime(replace(ingestion_time_utc,'Z','')) > datetime(replace(?,'Z',''), '-30 minutes')
                ORDER BY ingestion_time_utc
                """,
                (watermark,),
            ).fetchall()

        latest = {}
        for row in source:
            key = (row["record_id"], row["metric_type"])
            candidate = (row["source_last_modified_utc"], row["ingestion_time_utc"], row["event_id"])
            existing = latest.get(key)
            if existing is None or candidate > existing[0]:
                latest[key] = (candidate, row)

        upserts = deletes = 0
        for _, row in latest.values():
            current = conn.execute(
                "SELECT source_last_modified_utc FROM silver_metrics WHERE record_id=? AND metric_type=?",
                (row["record_id"], row["metric_type"]),
            ).fetchone()
            if current and current[0] > row["source_last_modified_utc"]:
                continue
            if row["operation"] == "DELETE":
                conn.execute(
                    "DELETE FROM silver_metrics WHERE record_id=? AND metric_type=?",
                    (row["record_id"], row["metric_type"]),
                )
                deletes += 1
            else:
                conn.execute(
                    """
                    INSERT INTO silver_metrics (
                        record_id, metric_type, user_id, device_id, event_time_utc,
                        end_time_utc, numeric_value, unit, sleep_stage,
                        source_last_modified_utc, ingestion_time_utc
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(record_id, metric_type) DO UPDATE SET
                        user_id=excluded.user_id,
                        device_id=excluded.device_id,
                        event_time_utc=excluded.event_time_utc,
                        end_time_utc=excluded.end_time_utc,
                        numeric_value=excluded.numeric_value,
                        unit=excluded.unit,
                        sleep_stage=excluded.sleep_stage,
                        source_last_modified_utc=excluded.source_last_modified_utc,
                        ingestion_time_utc=excluded.ingestion_time_utc
                    WHERE excluded.source_last_modified_utc >= silver_metrics.source_last_modified_utc
                    """,
                    (
                        row["record_id"], row["metric_type"], row["user_id"], row["device_id"],
                        row["event_time_utc"], row["end_time_utc"], row["numeric_value"], row["unit"],
                        row["sleep_stage"], row["source_last_modified_utc"], row["ingestion_time_utc"],
                    ),
                )
                upserts += 1

        new_watermark = watermark
        if source:
            new_watermark = max(r["ingestion_time_utc"] for r in source)
            conn.execute(
                "UPDATE pipeline_state SET watermark_utc=?, updated_utc=? WHERE pipeline_name='bronze_to_silver'",
                (new_watermark, iso(utc_now())),
            )

        _aggregate_gold(conn)
        _run_quality_checks(conn)
        completed = utc_now()
        duration_ms = max(1, int((time.perf_counter() - perf_started) * 1000))
        conn.execute(
            """
            INSERT INTO pipeline_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id, iso(started), iso(completed), "SUCCEEDED", len(source), len(latest),
                upserts, deletes, duration_ms, new_watermark,
            ),
        )
    return {
        "run_id": run_id,
        "input_rows": len(source),
        "deduplicated_rows": len(latest),
        "upserts": upserts,
        "deletes": deletes,
        "watermark": new_watermark,
    }


def _aggregate_gold(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM gold_daily_health")
    rows = conn.execute(
        "SELECT *, substr(event_time_utc,1,10) AS health_date FROM silver_metrics"
    ).fetchall()
    grouped: dict[tuple[str, str], list[sqlite3.Row]] = {}
    for r in rows:
        grouped.setdefault((r["health_date"], r["user_id"]), []).append(r)

    for (health_date, user_id), items in grouped.items():
        vals = {}
        for metric in ["heart_rate", "blood_oxygen", "skin_temperature"]:
            vals[metric] = [r["numeric_value"] for r in items if r["metric_type"] == metric and r["numeric_value"] is not None]
        def max_metric(metric):
            candidates = [r["numeric_value"] for r in items if r["metric_type"] == metric and r["numeric_value"] is not None]
            return max(candidates) if candidates else None
        def sum_stage(stage):
            return sum(r["numeric_value"] or 0 for r in items if r["metric_type"] == "sleep_stage" and r["sleep_stage"] == stage)
        hr = vals["heart_rate"]
        last_event = max((r["event_time_utc"] for r in items), default=None)
        conn.execute(
            """
            INSERT INTO gold_daily_health VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                health_date, user_id,
                int(max_metric("steps")) if max_metric("steps") is not None else None,
                sum(hr)/len(hr) if hr else None, min(hr) if hr else None, max(hr) if hr else None,
                sum(vals["blood_oxygen"])/len(vals["blood_oxygen"]) if vals["blood_oxygen"] else None,
                sum(vals["skin_temperature"])/len(vals["skin_temperature"]) if vals["skin_temperature"] else None,
                max_metric("sleep_session"), sum_stage("DEEP"), sum_stage("LIGHT"),
                sum_stage("REM"), sum_stage("AWAKE"), max_metric("energy_score"),
                last_event, iso(utc_now()),
            ),
        )


def _run_quality_checks(conn: sqlite3.Connection) -> None:
    checks = []
    dup = conn.execute(
        "SELECT COUNT(*) FROM (SELECT record_id, metric_type, COUNT(*) c FROM silver_metrics GROUP BY 1,2 HAVING c>1)"
    ).fetchone()[0]
    checks.append(("Unique business key", dup, "Silver record_id + metric_type"))
    missing = conn.execute(
        "SELECT COUNT(*) FROM silver_metrics WHERE record_id IS NULL OR metric_type IS NULL OR user_id IS NULL"
    ).fetchone()[0]
    checks.append(("Required fields", missing, "Required identifiers are populated"))
    plausible = conn.execute(
        """
        SELECT COUNT(*) FROM silver_metrics WHERE
        (metric_type='heart_rate' AND (numeric_value<20 OR numeric_value>250)) OR
        (metric_type='blood_oxygen' AND (numeric_value<50 OR numeric_value>100)) OR
        (metric_type='skin_temperature' AND (numeric_value<20 OR numeric_value>45)) OR
        (metric_type='steps' AND (numeric_value<0 OR numeric_value>100000))
        """
    ).fetchone()[0]
    checks.append(("Broad value plausibility", plausible, "Engineering guardrails; not clinical advice"))
    for name, failed, details in checks:
        conn.execute(
            "INSERT INTO data_quality VALUES (?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), iso(utc_now()), name, "PASS" if failed == 0 else "FAIL", failed, details),
        )


def fetch_df(query: str, params: Iterable | None = None):
    import pandas as pd
    with connect() as conn:
        return pd.read_sql_query(query, conn, params=params or ())
