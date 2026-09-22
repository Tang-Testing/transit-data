# Interview Prep — Transit Data Hub

Questions this project gives you a real, working answer to — plus
exactly what to point to in the repo when you answer, instead of
reciting a definition.

| Likely question | What to explain | Where in this repo |
|---|---|---|
| ETL vs. ELT — what's the difference? | Where transformation happens: here, validation/transformation happens in Python before the load | `etl/load_gps_events.py` |
| Why PostgreSQL? | Fits structured, relational transit data well; strong SQL, constraints, JSONB for the reject log | `sql/02_create_tables.sql` |
| How do you prevent duplicate data? | Natural key (`event_id`) + `ON CONFLICT DO NOTHING` at the database level, not app-level dedup logic | `etl/load_gps_events.py`, `tests/test_case01_duplicate_gps.py` |
| What do you do when a pipeline fails? | Explicit freshness check before loading, every run logged with status, rejects logged instead of crashing | `etl/run_pipeline.py`, `ops.etl_run_log` |
| Why separate Bronze / Silver / Gold? | Raw vs. cleaned vs. analytics-ready data — not yet built here, and you can say so honestly | See README Section 11 (Roadmap) |
| Why does data quality matter? | Bad data quietly breaks everything downstream; this pipeline makes bad data visible instead of hiding it | `ops.rejected_records`, README Section 8 |
| Why use Airflow (eventually)? | Scheduling, dependencies, retries, visibility into runs — this pipeline is currently run manually | README Section 11 (Roadmap) |
| How would you scale this to more data? | Incremental loading / watermarking, partitioning by date, batching | README Section 11 (Roadmap) |

Each answer should point to something real in this repo, not just a
definition — that's the reason to build the project instead of just
studying the concepts.
