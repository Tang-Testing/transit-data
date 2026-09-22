"""
Case 04 — Pipeline runs twice.

Scenario: Airflow retries the same task after a network error during
loading. Running the pipeline again on the same file must not change
the row count on the second run.
"""
from pathlib import Path

from etl.db import get_connection
from etl.load_gps_events import load_gps_events

GPS_FILE = Path("data/raw/gps_events_2026-09-21.csv")


def test_rerunning_load_is_idempotent():
    with get_connection() as conn:
        load_gps_events(conn, GPS_FILE)  # first run

        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM core.fact_gps_events")
            after_first = cur.fetchone()[0]

        load_gps_events(conn, GPS_FILE)  # simulated Airflow retry

        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM core.fact_gps_events")
            after_second = cur.fetchone()[0]

    assert after_first == after_second
