"""
Case 03 — Route code mismatch.

Scenario: a GPS event references route_id "R999", which does not
exist in the routes master. It must be separated out into
ops.rejected_records with a reason, not loaded with a broken foreign
key and not silently dropped.
"""
from pathlib import Path

from etl.db import get_connection
from etl.load_gps_events import load_gps_events

GPS_FILE = Path("data/raw/gps_events_2026-09-21.csv")


def test_unknown_route_id_is_rejected_not_loaded():
    with get_connection() as conn:
        result = load_gps_events(conn, GPS_FILE)

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) FROM ops.rejected_records
                WHERE source_table = 'fact_gps_events'
                  AND raw_data->>'route_id' = 'R999'
                """
            )
            rejected_count = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM core.fact_gps_events WHERE route_id = 'R999'")
            loaded_with_bad_route = cur.fetchone()[0]

    assert result["rejected"] >= 1
    assert rejected_count >= 1
    assert loaded_with_bad_route == 0
