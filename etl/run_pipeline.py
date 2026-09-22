"""
Daily pipeline entry point.

    python -m etl.run_pipeline --service-date 2026-09-21

Steps:
  1. Freshness check — does today's GPS file actually exist? (Case 02)
  2. Load dimension tables (idempotent upserts)
  3. Load GPS events (FK validation + duplicate-safe insert)
  4. Log the run to ops.etl_run_log
"""
import argparse
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from etl.config import DATA_DIR
from etl.db import get_connection
from etl.load_dimensions import load_routes, load_schedule, load_stops, load_vehicles
from etl.load_gps_events import load_gps_events


def check_freshness(service_date: str) -> Optional[Path]:
    """Case 02: has the GPS file for this service_date actually arrived?"""
    path = Path(DATA_DIR) / f"gps_events_{service_date}.csv"
    return path if path.exists() else None


def run(service_date: str) -> int:
    started = datetime.now()
    print(f"[{started.isoformat()}] Starting pipeline for service_date={service_date}")

    gps_path = check_freshness(service_date)
    if gps_path is None:
        expected = Path(DATA_DIR) / f"gps_events_{service_date}.csv"
        print(f"MISSING DATA: no GPS file found for {service_date} (expected {expected})")
        _log_run(service_date, started, status="FAILED_MISSING_FILE")
        return 1

    with get_connection() as conn:
        n_routes = load_routes(conn, Path(DATA_DIR) / "routes.csv")
        n_stops = load_stops(conn, Path(DATA_DIR) / "stops.csv")
        n_vehicles = load_vehicles(conn, Path(DATA_DIR) / "vehicles.csv")
        n_schedule = load_schedule(conn, Path(DATA_DIR) / "schedule.csv")
        gps_result = load_gps_events(conn, gps_path)

    print(f"Dimensions — routes: {n_routes}, stops: {n_stops}, "
          f"vehicles: {n_vehicles}, schedule: {n_schedule}")
    print(f"GPS events — loaded: {gps_result['loaded']}, "
          f"duplicates skipped: {gps_result['duplicates_skipped']}, "
          f"rejected: {gps_result['rejected']} / {gps_result['total_rows']}")

    _log_run(service_date, started, status="SUCCESS", gps_result=gps_result)
    return 0


def _log_run(service_date: str, started: datetime, status: str, gps_result: Optional[dict] = None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ops.etl_run_log
                    (pipeline_name, started_at, finished_at, status, rows_loaded, rows_rejected, message)
                VALUES (%s, %s, now(), %s, %s, %s, %s)
                """,
                (
                    "transit_data_hub_daily_load",
                    started,
                    status,
                    gps_result["loaded"] if gps_result else 0,
                    gps_result["rejected"] if gps_result else 0,
                    f"service_date={service_date}",
                ),
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--service-date", default=date.today().isoformat())
    args = parser.parse_args()
    sys.exit(run(args.service_date))
