from __future__ import annotations

import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

import db


class IncrementalPipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        db.DB_PATH = Path(self.temp.name) / 'test.db'
        db.initialize_db(reset=True)

    def tearDown(self):
        self.temp.cleanup()

    def test_newer_update_wins_and_rerun_is_idempotent(self):
        now = db.utc_now() - timedelta(minutes=10)
        record_id = 'hr-test-001'
        db.insert_event(db.make_event('heart_rate', now, 65, 'bpm', record_id=record_id, modified_delay=10))
        db.insert_event(db.make_event('heart_rate', now, 72, 'bpm', record_id=record_id, modified_delay=90))
        first = db.process_incremental()
        value = db.fetch_df("SELECT numeric_value FROM silver_metrics WHERE record_id=?", [record_id]).iloc[0,0]
        self.assertEqual(value, 72)
        self.assertEqual(db.fetch_df("SELECT COUNT(*) c FROM silver_metrics WHERE record_id=?", [record_id]).iloc[0,0], 1)
        db.process_incremental()
        self.assertEqual(db.fetch_df("SELECT COUNT(*) c FROM silver_metrics WHERE record_id=?", [record_id]).iloc[0,0], 1)
        self.assertGreaterEqual(first['deduplicated_rows'], 1)

    def test_delete_event_propagates_to_silver(self):
        now = db.utc_now() - timedelta(minutes=8)
        record_id = 'hr-delete-001'
        db.insert_event(db.make_event('heart_rate', now, 68, 'bpm', record_id=record_id, modified_delay=10))
        db.process_incremental()
        self.assertEqual(db.fetch_df("SELECT COUNT(*) c FROM silver_metrics WHERE record_id=?", [record_id]).iloc[0,0], 1)
        db.insert_event(db.make_event('heart_rate', now, None, 'bpm', record_id=record_id, operation='DELETE', modified_delay=120))
        db.process_incremental()
        self.assertEqual(db.fetch_df("SELECT COUNT(*) c FROM silver_metrics WHERE record_id=?", [record_id]).iloc[0,0], 0)

    def test_gold_and_quality_tables_are_created(self):
        now = db.utc_now() - timedelta(minutes=5)
        db.insert_event(db.make_event('steps', now, 9000, 'count'))
        db.insert_event(db.make_event('heart_rate', now, 70, 'bpm'))
        db.process_incremental()
        self.assertGreater(db.fetch_df('SELECT COUNT(*) c FROM gold_daily_health').iloc[0,0], 0)
        self.assertGreater(db.fetch_df('SELECT COUNT(*) c FROM data_quality').iloc[0,0], 0)
        self.assertEqual(db.fetch_df("SELECT COUNT(*) c FROM data_quality WHERE status='FAIL'").iloc[0,0], 0)


if __name__ == '__main__':
    unittest.main()
