CREATE TABLE budget_execution_owners (
    execution_id TEXT PRIMARY KEY REFERENCES execution_admissions (execution_id),
    policy_version TEXT NOT NULL CHECK (policy_version = 'f-009-budget-policy-v1'),
    player_scope_tag TEXT NOT NULL CHECK (length(player_scope_tag) = 64),
    npc_scope_tag TEXT NOT NULL CHECK (length(npc_scope_tag) = 64),
    player_npc_scope_tag TEXT NOT NULL CHECK (length(player_npc_scope_tag) = 64),
    created_at_ns INTEGER NOT NULL CHECK (created_at_ns > 0)
) STRICT;

CREATE INDEX idx_budget_owners_player
    ON budget_execution_owners (player_scope_tag, created_at_ns DESC);
CREATE INDEX idx_budget_owners_npc
    ON budget_execution_owners (npc_scope_tag, created_at_ns DESC);
CREATE INDEX idx_budget_owners_player_npc
    ON budget_execution_owners (player_npc_scope_tag, created_at_ns DESC);

CREATE TABLE budget_reservations (
    execution_id TEXT NOT NULL REFERENCES budget_execution_owners (execution_id),
    attempt_number INTEGER NOT NULL CHECK (attempt_number BETWEEN 1 AND 2),
    policy_version TEXT NOT NULL CHECK (policy_version = 'f-009-budget-policy-v1'),
    pricing_version TEXT NOT NULL CHECK (length(pricing_version) BETWEEN 1 AND 64),
    provider_kind TEXT NOT NULL CHECK (
        provider_kind IN ('fake', 'deepseek', 'local-fallback', 'disabled', 'unknown')
    ),
    provider_model TEXT NOT NULL CHECK (length(provider_model) BETWEEN 1 AND 128),
    reserved_micro_usd INTEGER NOT NULL CHECK (
        reserved_micro_usd BETWEEN 0 AND 2000
    ),
    soft_warning INTEGER NOT NULL CHECK (soft_warning IN (0, 1)),
    status TEXT NOT NULL CHECK (
        status IN ('reserved', 'dispatched', 'settled', 'released')
    ),
    reserved_at_ns INTEGER NOT NULL CHECK (reserved_at_ns > 0),
    dispatched_at_ns INTEGER CHECK (
        dispatched_at_ns IS NULL OR dispatched_at_ns >= reserved_at_ns
    ),
    settled_at_ns INTEGER CHECK (
        settled_at_ns IS NULL OR settled_at_ns >= reserved_at_ns
    ),
    released_at_ns INTEGER CHECK (
        released_at_ns IS NULL OR released_at_ns >= reserved_at_ns
    ),
    release_reason TEXT CHECK (
        release_reason IS NULL OR release_reason = 'cancelled_before_dispatch'
    ),
    PRIMARY KEY (execution_id, attempt_number),
    CHECK (
        (status = 'reserved' AND dispatched_at_ns IS NULL AND settled_at_ns IS NULL
            AND released_at_ns IS NULL AND release_reason IS NULL)
        OR
        (status = 'dispatched' AND dispatched_at_ns IS NOT NULL AND settled_at_ns IS NULL
            AND released_at_ns IS NULL AND release_reason IS NULL)
        OR
        (status = 'settled' AND dispatched_at_ns IS NOT NULL AND settled_at_ns IS NOT NULL
            AND released_at_ns IS NULL AND release_reason IS NULL)
        OR
        (status = 'released' AND dispatched_at_ns IS NULL AND settled_at_ns IS NULL
            AND released_at_ns IS NOT NULL AND release_reason IS NOT NULL)
    )
) STRICT;

CREATE INDEX idx_budget_attempt_quota_time
    ON budget_reservations (reserved_at_ns DESC, status);
CREATE INDEX idx_budget_attempt_execution_status
    ON budget_reservations (execution_id, status, attempt_number);

CREATE TABLE budget_settlements (
    execution_id TEXT NOT NULL,
    attempt_number INTEGER NOT NULL,
    policy_version TEXT NOT NULL CHECK (policy_version = 'f-009-budget-policy-v1'),
    pricing_version TEXT NOT NULL CHECK (length(pricing_version) BETWEEN 1 AND 64),
    reserved_micro_usd INTEGER NOT NULL CHECK (reserved_micro_usd BETWEEN 0 AND 2000),
    actual_cost_micro_usd INTEGER NOT NULL CHECK (
        actual_cost_micro_usd BETWEEN 0 AND reserved_micro_usd
    ),
    released_micro_usd INTEGER NOT NULL CHECK (
        released_micro_usd >= 0
        AND actual_cost_micro_usd + released_micro_usd = reserved_micro_usd
    ),
    prompt_tokens INTEGER NOT NULL CHECK (prompt_tokens BETWEEN 0 AND 32768),
    completion_tokens INTEGER NOT NULL CHECK (completion_tokens BETWEEN 0 AND 256),
    conservative INTEGER NOT NULL CHECK (conservative IN (0, 1)),
    reason TEXT NOT NULL CHECK (
        reason IN (
            'trusted_usage', 'provider_timeout', 'provider_unavailable',
            'provider_invalid_response', 'cancelled_after_dispatch', 'internal_error',
            'abandoned_after_restart'
        )
    ),
    settled_at_ns INTEGER NOT NULL CHECK (settled_at_ns > 0),
    PRIMARY KEY (execution_id, attempt_number),
    FOREIGN KEY (execution_id, attempt_number)
        REFERENCES budget_reservations (execution_id, attempt_number)
) STRICT;

CREATE INDEX idx_budget_cost_window_time
    ON budget_settlements (settled_at_ns DESC, actual_cost_micro_usd);

PRAGMA user_version = 2;
