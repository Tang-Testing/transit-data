"""
Generate mock data for the Transit Data Hub project.

Produces 5 CSV files under data/raw/:
    routes.csv, stops.csv, vehicles.csv, schedule.csv,
    gps_events_<SERVICE_DATE>.csv

Two data-quality problems are injected on purpose, matching the
scenario tests in tests/:
  - Case 01: one duplicate event_id in the GPS file (simulated retry)
  - Case 03: one GPS row references route_id "R999", which does not
             exist in routes.csv (referential integrity failure)

Case 02 (late/missing file) is tested by *not* generating a GPS file
for "today" (2026-09-22) — only 2026-09-21 gets one. Case 04
(idempotent retry) is tested by running the loader twice against the
same file, not by anything in the data itself.

Run:
    python scripts/generate_mock_data.py
"""
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "raw"
SERVICE_DATE = "2026-09-21"  # the only day that gets a GPS file

ROUTES = [
    ("R001", "Mo Chit - Bang Na", "Bus", "BMTA"),
    ("R002", "Victory Monument - Lat Krabang", "Bus", "BMTA"),
    ("R003", "Siam - On Nut", "BTS", "BTSC"),
    ("R004", "Hua Lamphong - Bang Sue", "MRT", "MRTA"),
    ("R005", "Ratchada - Lat Phrao", "Bus", "BMTA"),
    ("R006", "Ekkamai - Bang Kapi", "Bus", "BMTA"),
    ("R007", "Chatuchak - Don Mueang", "Bus", "BMTA"),
    ("R008", "Asok - Udomsuk", "BTS", "BTSC"),
]

# rough bounding box over central Bangkok — just for plausible-looking points
LAT_RANGE = (13.65, 13.90)
LON_RANGE = (100.45, 100.65)


def rand_point():
    return round(random.uniform(*LAT_RANGE), 6), round(random.uniform(*LON_RANGE), 6)


def write_routes():
    path = OUT_DIR / "routes.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["route_id", "route_name", "route_type", "operator"])
        w.writerows(ROUTES)
    return path


def write_stops():
    path = OUT_DIR / "stops.csv"
    rows = []
    stop_num = 1
    for route_id, route_name, *_ in ROUTES:
        prefix = route_name.split(" - ")[0]
        for seq in range(1, 4):  # 3 stops per route
            lat, lon = rand_point()
            rows.append((f"S{stop_num:03d}", f"{prefix} Stop {seq}", route_id, seq, lat, lon))
            stop_num += 1
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["stop_id", "stop_name", "route_id", "sequence", "latitude", "longitude"])
        w.writerows(rows)
    return path


def write_vehicles():
    path = OUT_DIR / "vehicles.csv"
    rows = []
    veh_num = 1
    for route_id, _, route_type, _ in ROUTES:
        for _ in range(2):  # 2 vehicles per route
            plate = (f"{random.randint(1, 9)}{random.choice('กขคงจ')}"
                     f"{random.choice('กขคงจ')}-{random.randint(1000, 9999)}")
            capacity = 50 if route_type == "Bus" else 200
            rows.append((f"V{veh_num:03d}", route_id, route_type, capacity, plate))
            veh_num += 1
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["vehicle_id", "route_id", "vehicle_type", "capacity", "plate_no"])
        w.writerows(rows)
    return path, rows


def write_schedule(vehicles):
    path = OUT_DIR / "schedule.csv"
    by_route = {}
    for vehicle_id, route_id, *_ in vehicles:
        by_route.setdefault(route_id, []).append(vehicle_id)

    rows = []
    departures = ["06:00", "12:00", "17:00"]
    for route_id, veh_ids in by_route.items():
        for i, dep_str in enumerate(departures):
            vehicle_id = veh_ids[i % len(veh_ids)]
            dep = datetime.strptime(f"{SERVICE_DATE} {dep_str}", "%Y-%m-%d %H:%M")
            arr = dep + timedelta(minutes=45)
            rows.append((
                f"T-{route_id}-{i + 1:02d}", route_id, vehicle_id, SERVICE_DATE,
                dep.strftime("%Y-%m-%d %H:%M:%S"), arr.strftime("%Y-%m-%d %H:%M:%S"),
            ))
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["trip_id", "route_id", "vehicle_id", "service_date",
                     "scheduled_departure", "scheduled_arrival"])
        w.writerows(rows)
    return path, rows


def write_gps_events(schedule_rows):
    path = OUT_DIR / f"gps_events_{SERVICE_DATE}.csv"
    rows = []
    event_num = 1
    for trip_id, route_id, vehicle_id, service_date, dep_str, arr_str in schedule_rows:
        dep = datetime.strptime(dep_str, "%Y-%m-%d %H:%M:%S")
        arr = datetime.strptime(arr_str, "%Y-%m-%d %H:%M:%S")
        n_pings = 5
        step = (arr - dep) / (n_pings - 1)
        for i in range(n_pings):
            ts = dep + step * i
            lat, lon = rand_point()
            speed = round(random.uniform(10, 55), 1)
            rows.append([f"EVT{event_num:05d}", vehicle_id, route_id,
                         ts.strftime("%Y-%m-%d %H:%M:%S"), lat, lon, speed])
            event_num += 1

    # --- inject Case 03: one GPS ping references a route not in routes.csv ---
    rows[30][2] = "R999"

    # --- inject Case 01: duplicate an existing event_id (simulated retry) ---
    rows.insert(50, rows[10].copy())

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["event_id", "vehicle_id", "route_id", "event_timestamp",
                     "latitude", "longitude", "speed_kmh"])
        w.writerows(rows)
    return path, rows


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_routes()
    write_stops()
    _, vehicles = write_vehicles()
    _, schedule_rows = write_schedule(vehicles)
    gps_path, gps_rows = write_gps_events(schedule_rows)

    print("Wrote routes.csv, stops.csv, vehicles.csv, schedule.csv")
    print(f"Wrote {gps_path.name} ({len(gps_rows)} rows — "
          f"includes 1 duplicate event_id + 1 unknown route_id for testing)")
    print("No GPS file created for 2026-09-22 on purpose (Case 02: missing file)")


if __name__ == "__main__":
    main()
