CREATE TABLE retry_breaker_events (
    trace_id TEXT NOT NULL REFERENCES trace_runs(trace_id),
    execution_id TEXT NOT NULL CHECK (length(execution_id) = 36),
    attempt_number INTEGER NOT NULL CHECK (attempt_number BETWEEN 0 AND 2),
    event_kind TEXT NOT NULL CHECK (event_kind IN (
        'breaker_check', 'retry_scheduled', 'attempt', 'breaker_result', 'probe_release'
    )),
    policy_version TEXT NOT NULL CHECK (policy_version = 'f-009-retry-breaker-v1'),
    retry_outcome TEXT NOT NULL CHECK (retry_outcome IN (
        'not_reached', 'not_eligible', 'scheduled', 'attempted', 'exhausted', 'cancelled'
    )),
    breaker_state TEXT NOT NULL CHECK (breaker_state IN ('closed', 'open', 'half_open')),
    breaker_outcome TEXT NOT NULL CHECK (breaker_outcome IN (
        'not_reached', 'allowed', 'rejected', 'probe_allowed', 'transitioned', 'failed'
    )),
    failure_reason TEXT CHECK (failure_reason IS NULL OR failure_reason IN (
        'provider_timeout', 'provider_unavailable', 'provider_invalid_response'
    )),
    backoff_ms INTEGER NOT NULL CHECK (backoff_ms BETWEEN 0 AND 400),
    jitter_ms INTEGER NOT NULL CHECK (jitter_ms BETWEEN 0 AND 200),
    deadline_remaining_ms INTEGER NOT NULL CHECK (
        deadline_remaining_ms BETWEEN 0 AND 12000
    ),
    recorded_at_ms INTEGER NOT NULL CHECK (recorded_at_ms > 0),
    PRIMARY KEY (trace_id, attempt_number, event_kind)
) STRICT;

CREATE INDEX retry_breaker_execution_attempt_idx
ON retry_breaker_events(execution_id, attempt_number, recorded_at_ms);

PRAGMA user_version = 3;
