CREATE TABLE IF NOT EXISTS readings (
    id BIGSERIAL PRIMARY KEY,
    sensor_id TEXT NOT NULL,
    metric TEXT NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    unit TEXT NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS readings_recorded_at_idx ON readings (recorded_at);
CREATE INDEX IF NOT EXISTS readings_sensor_metric_idx ON readings (sensor_id, metric, recorded_at);
