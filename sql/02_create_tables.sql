-- ============================================================
-- core: reference (dimension) tables
-- ============================================================

CREATE TABLE IF NOT EXISTS core.dim_routes (
    route_id    VARCHAR(10) PRIMARY KEY,
    route_name  VARCHAR(100) NOT NULL,
    route_type  VARCHAR(20) NOT NULL,
    operator    VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS core.dim_stops (
    stop_id     VARCHAR(10) PRIMARY KEY,
    stop_name   VARCHAR(100) NOT NULL,
    route_id    VARCHAR(10) NOT NULL REFERENCES core.dim_routes(route_id),
    sequence    INT NOT NULL,
    latitude    NUMERIC(9,6) NOT NULL,
    longitude   NUMERIC(9,6) NOT NULL
);

CREATE TABLE IF NOT EXISTS core.dim_vehicles (
    vehicle_id    VARCHAR(10) PRIMARY KEY,
    route_id      VARCHAR(10) NOT NULL REFERENCES core.dim_routes(route_id),
    vehicle_type  VARCHAR(20) NOT NULL,
    capacity      INT NOT NULL,
    plate_no      VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS core.dim_schedule (
    trip_id              VARCHAR(20) PRIMARY KEY,
    route_id             VARCHAR(10) NOT NULL REFERENCES core.dim_routes(route_id),
    vehicle_id           VARCHAR(10) NOT NULL REFERENCES core.dim_vehicles(vehicle_id),
    service_date         DATE NOT NULL,
    scheduled_departure  TIMESTAMP NOT NULL,
    scheduled_arrival    TIMESTAMP NOT NULL
);

-- ============================================================
-- core: fact table
-- ============================================================

CREATE TABLE IF NOT EXISTS core.fact_gps_events (
    event_id         VARCHAR(20) PRIMARY KEY,
    vehicle_id       VARCHAR(10) NOT NULL REFERENCES core.dim_vehicles(vehicle_id),
    route_id         VARCHAR(10) NOT NULL REFERENCES core.dim_routes(route_id),
    event_timestamp  TIMESTAMP NOT NULL,
    latitude         NUMERIC(9,6) NOT NULL,
    longitude        NUMERIC(9,6) NOT NULL,
    speed_kmh        NUMERIC(5,2),
    loaded_at        TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_fact_gps_events_route_id ON core.fact_gps_events(route_id);
CREATE INDEX IF NOT EXISTS idx_fact_gps_events_vehicle_id ON core.fact_gps_events(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_fact_gps_events_timestamp ON core.fact_gps_events(event_timestamp);

-- ============================================================
-- ops: pipeline bookkeeping
-- ============================================================

CREATE TABLE IF NOT EXISTS ops.rejected_records (
    rejected_id    SERIAL PRIMARY KEY,
    source_table   VARCHAR(50) NOT NULL,
    raw_data       JSONB NOT NULL,
    reject_reason  TEXT NOT NULL,
    rejected_at    TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ops.etl_run_log (
    run_id         SERIAL PRIMARY KEY,
    pipeline_name  VARCHAR(100) NOT NULL,
    started_at     TIMESTAMP NOT NULL,
    finished_at    TIMESTAMP,
    status         VARCHAR(30) NOT NULL,
    rows_loaded    INT DEFAULT 0,
    rows_rejected  INT DEFAULT 0,
    message        TEXT
);
