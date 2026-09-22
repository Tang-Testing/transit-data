"""
Shared fixtures for the scenario tests.

These tests are integration tests: they need the docker-compose
Postgres running with the schema already created (docker compose up -d
does both, via sql/ mounted as docker-entrypoint-initdb.d).
"""
from pathlib import Path

import pytest

from etl.db import get_connection
from etl.load_dimensions import load_routes, load_schedule, load_stops, load_vehicles

DATA_DIR = Path("data/raw")


@pytest.fixture(scope="session", autouse=True)
def load_reference_data():
    """Ensure dimension tables are populated before any scenario test runs."""
    with get_connection() as conn:
        load_routes(conn, DATA_DIR / "routes.csv")
        load_stops(conn, DATA_DIR / "stops.csv")
        load_vehicles(conn, DATA_DIR / "vehicles.csv")
        load_schedule(conn, DATA_DIR / "schedule.csv")
    yield
