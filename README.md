# Transit Data Hub

## End-to-End Public Transit Data Engineering Platform (MVP)

## 1. Project Overview

Transit Data Hub is a data engineering portfolio project that
integrates simulated public transit data — routes, stops, vehicles,
schedules, and GPS pings — from CSV sources into a PostgreSQL
warehouse, with data-quality checks and pipeline logging built in
from the start, not bolted on afterward.

This repo currently implements **Milestone 1**: mock data generation,
a PostgreSQL schema, and a Python ETL pipeline. See
[Section 11](#11-limitations--roadmap) for what's next.

## 2. Business Problem

Transit data is typically scattered across multiple systems (route
planning, vehicle telemetry, scheduling), which makes it hard to
monitor service performance or trust the numbers without a validated,
single source of truth. This project builds a small but realistic
ETL pipeline that ingests, validates, and loads that data — and is
explicitly tested against the kind of failures a real pipeline hits:
duplicate events, late files, bad foreign keys, and retried jobs.

## 3. Architecture

```
CSV sources (routes, stops, vehicles, schedule, GPS events)
        |
        v
  Python ETL (etl/) -- validates + upserts --> PostgreSQL
        |                                        +-- core  (dim_*, fact_gps_events)
        v                                        +-- ops   (rejected_records, etl_run_log)
  Rejected / duplicate rows are logged, never silently dropped
```

A full Bronze -> Silver -> Gold layering is on the roadmap (Section 11);
the current MVP loads validated data straight into the `core` schema,
with a separate `ops` schema for anything the pipeline rejects or logs.

## 4. Tech Stack

- Python (psycopg2)
- PostgreSQL 16
- Docker / docker-compose
- pytest
- Planned: Apache Airflow, Pandera, Power BI — see Section 11

## 5. Key Features

- Multi-source mock data ingestion (routes, stops, vehicles, schedule, GPS)
- Idempotent upserts for all dimension tables
- Duplicate-safe GPS event loading (`ON CONFLICT DO NOTHING` on `event_id`)
- Referential-integrity validation (unknown `route_id` / `vehicle_id` -> rejected, not loaded)
- Freshness check for the day's GPS file, with a documented failure case
- Every pipeline run logged to `ops.etl_run_log`

## 6. Project Structure

```
transit-data-hub/
├── scripts/generate_mock_data.py   # builds the 5 CSVs below (seeded, reproducible)
├── data/raw/                       # routes, stops, vehicles, schedule, gps_events_*.csv
├── sql/                             # schema + table DDL (auto-run by docker-compose)
├── etl/                             # config, db connection, loaders, pipeline entry point
├── tests/                           # one test file per scenario case (Section 9)
├── docs/interview_prep.md           # talking points this project backs up
├── docker-compose.yml
└── requirements.txt
```

## 7. How to Run

### Clone and configure
```bash
git clone <YOUR_REPOSITORY_URL>
cd transit-data-hub
cp .env.example .env
pip install -r requirements.txt --break-system-packages
```

### Start PostgreSQL
Schema and tables are created automatically on first start (via the
`sql/` folder mounted as `docker-entrypoint-initdb.d`):
```bash
docker compose up -d
```

### Regenerate the mock data (already included, but reproducible)
```bash
python scripts/generate_mock_data.py
```

### Run the pipeline
```bash
python -m etl.run_pipeline --service-date 2026-09-21
```

### Run the scenario tests
```bash
pytest -v
```

## 8. Data Quality

| Check        | Description                                       | Status |
|--------------|----------------------------------------------------|--------|
| Duplicate ID | A retried `event_id` is not loaded twice            | Implemented — `ON CONFLICT DO NOTHING` |
| FK Check     | `route_id` / `vehicle_id` must exist in the dims    | Implemented — rejected rows go to `ops.rejected_records` |
| Freshness    | Today's GPS file must actually exist before loading | Implemented — `check_freshness()` |
| Null Check   | Required fields must be populated                   | Not yet — planned with Pandera, Section 11 |

## 9. Scenario-Based Testing

Four operational incidents a data engineer would realistically hit,
each backed by its own test in `tests/`:

| Case | Scenario                                                    | Test file |
|------|--------------------------------------------------------------|-----------|
| 01   | A GPS event is retried and arrives twice with the same `event_id` | `test_case01_duplicate_gps.py` |
| 02   | The day's GPS file hasn't arrived yet                        | `test_case02_missing_file.py` |
| 03   | A GPS ping references a `route_id` not in the routes master  | `test_case03_route_mismatch.py` |
| 04   | Airflow-style retry re-runs the same load after a network error | `test_case04_idempotency.py` |

## 10. Results

Not yet measured — run the pipeline and tests yourself (Section 7)
and fill this in with real numbers instead of estimates.

- Total records processed: _TBD_
- Records rejected: _TBD_
- Pipeline execution time: _TBD_

## 11. Limitations & Roadmap

**Current limitations**
- Data is simulated (`scripts/generate_mock_data.py`), not a real transit feed
- No Bronze / Silver / Gold layering yet — validated data loads straight into `core`
- No orchestration yet — the pipeline is run manually, not via Airflow
- No dashboard yet

**Planned next** (see the MVP checklist this project is built from)
- [ ] Formal data-quality layer with Pandera (null checks, schema contracts)
- [ ] Incremental loading (watermarking, not just one file per run)
- [ ] Airflow DAG wrapping `etl.run_pipeline`, with retries and alerting
- [ ] Data mart + Power BI dashboard

## 12. Author

Phongpeera Thepdecha ("Nice")
