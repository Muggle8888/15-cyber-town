CREATE TABLE control_execution_intents (
    execution_id TEXT NOT NULL,
    attempt_number INTEGER NOT NULL CHECK (attempt_number BETWEEN 1 AND 2),
    policy_version TEXT NOT NULL CHECK (
        policy_version = 'f-009-control-execution-intent-v1'
    ),
    state TEXT NOT NULL CHECK (state IN ('dispatch_intent', 'released', 'settled')),
    conservative INTEGER NOT NULL CHECK (conservative IN (0, 1)),
    created_at_ns INTEGER NOT NULL CHECK (created_at_ns > 0),
    finalized_at_ns INTEGER CHECK (
        finalized_at_ns IS NULL OR finalized_at_ns >= created_at_ns
    ),
    terminal_reason TEXT CHECK (
        terminal_reason IS NULL OR terminal_reason IN (
            'trusted_usage', 'provider_timeout', 'provider_unavailable',
            'provider_invalid_response', 'cancelled_after_dispatch', 'internal_error',
            'abandoned_after_restart', 'cancelled_before_dispatch'
        )
    ),
    revision INTEGER NOT NULL CHECK (revision >= 1),
    PRIMARY KEY (execution_id, attempt_number),
    FOREIGN KEY (execution_id, attempt_number)
        REFERENCES budget_reservations(execution_id, attempt_number) ON DELETE RESTRICT,
    CHECK (
        (state = 'dispatch_intent' AND conservative = 0
            AND finalized_at_ns IS NULL AND terminal_reason IS NULL)
        OR
        (state = 'released' AND conservative = 0
            AND finalized_at_ns IS NOT NULL
            AND terminal_reason = 'cancelled_before_dispatch')
        OR
        (state = 'settled' AND finalized_at_ns IS NOT NULL
            AND terminal_reason IS NOT NULL
            AND terminal_reason <> 'cancelled_before_dispatch')
    )
) STRICT, WITHOUT ROWID;

PRAGMA user_version = 6;
