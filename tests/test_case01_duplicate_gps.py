"""
Case 01 — Duplicate GPS data.

Scenario: the source system resends an event with the same event_id
after a retry. The pipeline must detect the duplicate and must not
insert a second row into the fact table.
"""
from pathlib import Path

from etl.db import get_connection
from etl.load_gps_events import load_gps_events

GPS_FILE = Path("data/raw/gps_events_2026-09-21.csv")


def test_duplicate_event_id_is_not_double_loaded():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM core.fact_gps_events")
            before = cur.fetchone()[0]

        result = load_gps_events(conn, GPS_FILE)

        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM core.fact_gps_events")
            after = cur.fetchone()[0]

    # the mock file contains one duplicated event_id, so it must be caught
    assert result["duplicates_skipped"] >= 1
    # the fact table only grows by "loaded", never by the raw row count
    assert after - before == result["loaded"]
