"""
Loader for the GPS events fact table.

Two data-quality rules are enforced here, matching the project's
scenario tests (see tests/ and README Section 9):

  - Case 03: a row whose route_id or vehicle_id doesn't exist in the
    dimension tables is rejected into ops.rejected_records instead of
    breaking a foreign key or silently vanishing.

  - Case 01 / Case 04: event_id is the natural key. Loading uses
    ON CONFLICT (event_id) DO NOTHING, so a retried event (the same
    event_id sent twice) or a full pipeline re-run never creates
    duplicate rows in core.fact_gps_events.
"""
import csv
import json
from pathlib import Path


def _read_csv(path: Path):
    with open(path, newline="", encoding="utf-8") as f:
        yield from csv.DictReader(f)


def _valid_ids(cur, table: str, column: str) -> set:
    cur.execute(f"SELECT {column} FROM {table}")
    return {row[0] for row in cur.fetchall()}


def load_gps_events(conn, path: Path) -> dict:
    rows = list(_read_csv(path))
    loaded = 0
    duplicates_skipped = 0
    rejected = 0

    with conn.cursor() as cur:
        valid_routes = _valid_ids(cur, "core.dim_routes", "route_id")
        valid_vehicles = _valid_ids(cur, "core.dim_vehicles", "vehicle_id")

        for r in rows:
            if r["route_id"] not in valid_routes or r["vehicle_id"] not in valid_vehicles:
                cur.execute(
                    """
                    INSERT INTO ops.rejected_records (source_table, raw_data, reject_reason)
                    VALUES (%s, %s, %s)
                    """,
                    (
                        "fact_gps_events",
                        json.dumps(r),
                        f"Unknown route_id={r['route_id']!r} or vehicle_id={r['vehicle_id']!r}",
                    ),
                )
                rejected += 1
                continue

            cur.execute(
                """
                INSERT INTO core.fact_gps_events
                    (event_id, vehicle_id, route_id, event_timestamp, latitude, longitude, speed_kmh)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (event_id) DO NOTHING
                """,
                (r["event_id"], r["vehicle_id"], r["route_id"], r["event_timestamp"],
                 r["latitude"], r["longitude"], r["speed_kmh"]),
            )
            if cur.rowcount == 0:
                duplicates_skipped += 1
            else:
                loaded += 1

    return {
        "total_rows": len(rows),
        "loaded": loaded,
        "duplicates_skipped": duplicates_skipped,
        "rejected": rejected,
    }
