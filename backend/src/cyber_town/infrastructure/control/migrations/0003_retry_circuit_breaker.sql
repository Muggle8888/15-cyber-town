CREATE TABLE circuit_breakers (
    scope_tag TEXT PRIMARY KEY CHECK (
        length(scope_tag) = 64 AND scope_tag NOT GLOB '*[^0-9a-f]*'
    ),
    policy_version TEXT NOT NULL CHECK (
        policy_version = 'f-009-retry-breaker-v1'
    ),
    state TEXT NOT NULL CHECK (state IN ('closed', 'open', 'half_open')),
    failure_count INTEGER NOT NULL CHECK (failure_count BETWEEN 0 AND 5),
    failure_window_started_ns INTEGER CHECK (failure_window_started_ns > 0),
    open_until_ns INTEGER CHECK (open_until_ns > 0),
    probe_success_count INTEGER NOT NULL CHECK (probe_success_count BETWEEN 0 AND 1),
    updated_at_ns INTEGER NOT NULL CHECK (updated_at_ns > 0),
    CHECK (
        (state = 'open' AND open_until_ns IS NOT NULL)
        OR (state <> 'open' AND open_until_ns IS NULL)
    )
) STRICT;

CREATE TABLE breaker_probe_leases (
    scope_tag TEXT PRIMARY KEY
        REFERENCES circuit_breakers(scope_tag) ON DELETE RESTRICT,
    execution_id TEXT NOT NULL UNIQUE CHECK (length(execution_id) = 36),
    acquired_at_ns INTEGER NOT NULL CHECK (acquired_at_ns > 0)
) STRICT;

CREATE TABLE breaker_execution_results (
    execution_id TEXT PRIMARY KEY CHECK (length(execution_id) = 36),
    scope_tag TEXT NOT NULL
        REFERENCES circuit_breakers(scope_tag) ON DELETE RESTRICT,
    outcome TEXT NOT NULL CHECK (outcome IN ('success', 'failure')),
    failure_reason TEXT CHECK (
        failure_reason IS NULL OR failure_reason IN (
            'provider_timeout', 'provider_unavailable', 'provider_invalid_response'
        )
    ),
    recorded_at_ns INTEGER NOT NULL CHECK (recorded_at_ns > 0),
    CHECK (
        (outcome = 'success' AND failure_reason IS NULL)
        OR (outcome = 'failure' AND failure_reason IS NOT NULL)
    )
) STRICT;

CREATE INDEX breaker_results_scope_time_idx
ON breaker_execution_results(scope_tag, recorded_at_ns DESC);

PRAGMA user_version = 3;
