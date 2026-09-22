"""
Loaders for the dimension tables (routes, stops, vehicles, schedule).

Each loader upserts by primary key, so re-running the pipeline on the
same reference files never creates duplicates or fails on a re-run.
"""
import csv
from pathlib import Path


def _read_csv(path: Path):
    with open(path, newline="", encoding="utf-8") as f:
        yield from csv.DictReader(f)


def load_routes(conn, path: Path) -> int:
    rows = list(_read_csv(path))
    with conn.cursor() as cur:
        for r in rows:
            cur.execute(
                """
                INSERT INTO core.dim_routes (route_id, route_name, route_type, operator)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (route_id) DO UPDATE SET
                    route_name = EXCLUDED.route_name,
                    route_type = EXCLUDED.route_type,
                    operator = EXCLUDED.operator
                """,
                (r["route_id"], r["route_name"], r["route_type"], r["operator"]),
            )
    return len(rows)


def load_stops(conn, path: Path) -> int:
    rows = list(_read_csv(path))
    with conn.cursor() as cur:
        for r in rows:
            cur.execute(
                """
                INSERT INTO core.dim_stops (stop_id, stop_name, route_id, sequence, latitude, longitude)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (stop_id) DO UPDATE SET
                    stop_name = EXCLUDED.stop_name,
                    route_id = EXCLUDED.route_id,
                    sequence = EXCLUDED.sequence,
                    latitude = EXCLUDED.latitude,
                    longitude = EXCLUDED.longitude
                """,
                (r["stop_id"], r["stop_name"], r["route_id"], r["sequence"],
                 r["latitude"], r["longitude"]),
            )
    return len(rows)


def load_vehicles(conn, path: Path) -> int:
    rows = list(_read_csv(path))
    with conn.cursor() as cur:
        for r in rows:
            cur.execute(
                """
                INSERT INTO core.dim_vehicles (vehicle_id, route_id, vehicle_type, capacity, plate_no)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (vehicle_id) DO UPDATE SET
                    route_id = EXCLUDED.route_id,
                    vehicle_type = EXCLUDED.vehicle_type,
                    capacity = EXCLUDED.capacity,
                    plate_no = EXCLUDED.plate_no
                """,
                (r["vehicle_id"], r["route_id"], r["vehicle_type"], r["capacity"], r["plate_no"]),
            )
    return len(rows)


def load_schedule(conn, path: Path) -> int:
    rows = list(_read_csv(path))
    with conn.cursor() as cur:
        for r in rows:
            cur.execute(
                """
                INSERT INTO core.dim_schedule
                    (trip_id, route_id, vehicle_id, service_date, scheduled_departure, scheduled_arrival)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (trip_id) DO UPDATE SET
                    route_id = EXCLUDED.route_id,
                    vehicle_id = EXCLUDED.vehicle_id,
                    service_date = EXCLUDED.service_date,
                    scheduled_departure = EXCLUDED.scheduled_departure,
                    scheduled_arrival = EXCLUDED.scheduled_arrival
                """,
                (r["trip_id"], r["route_id"], r["vehicle_id"], r["service_date"],
                 r["scheduled_departure"], r["scheduled_arrival"]),
            )
    return len(rows)
