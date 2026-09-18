CREATE TABLE safety_cost_events (
    trace_id TEXT NOT NULL REFERENCES trace_runs (trace_id),
    execution_id TEXT NOT NULL CHECK (length(execution_id) = 36),
    attempt_number INTEGER NOT NULL CHECK (attempt_number BETWEEN 1 AND 2),
    event_kind TEXT NOT NULL CHECK (
        event_kind IN ('reservation', 'dispatch', 'settlement', 'release', 'rejection')
    ),
    policy_version TEXT NOT NULL CHECK (policy_version = 'f-009-budget-policy-v1'),
    pricing_version TEXT NOT NULL CHECK (length(pricing_version) BETWEEN 1 AND 64),
    provider_kind TEXT NOT NULL CHECK (
        provider_kind IN ('fake', 'deepseek', 'local-fallback', 'disabled', 'unknown')
    ),
    outcome TEXT NOT NULL CHECK (
        outcome IN ('not_reached', 'reserved', 'settled', 'rejected', 'failed')
    ),
    player_scope_tag TEXT NOT NULL CHECK (length(player_scope_tag) = 64),
    npc_scope_tag TEXT NOT NULL CHECK (length(npc_scope_tag) = 64),
    player_npc_scope_tag TEXT NOT NULL CHECK (length(player_npc_scope_tag) = 64),
    reserved_micro_usd INTEGER NOT NULL CHECK (reserved_micro_usd BETWEEN 0 AND 2000),
    actual_cost_micro_usd INTEGER NOT NULL CHECK (
        actual_cost_micro_usd BETWEEN 0 AND reserved_micro_usd
    ),
    prompt_tokens INTEGER NOT NULL CHECK (prompt_tokens BETWEEN 0 AND 32768),
    completion_tokens INTEGER NOT NULL CHECK (completion_tokens BETWEEN 0 AND 256),
    conservative INTEGER NOT NULL CHECK (conservative IN (0, 1)),
    recorded_at_ms INTEGER NOT NULL CHECK (recorded_at_ms > 0),
    PRIMARY KEY (trace_id, attempt_number, event_kind)
) STRICT;

CREATE INDEX idx_safety_cost_execution_attempt
    ON safety_cost_events (execution_id, attempt_number, recorded_at_ms);
CREATE INDEX idx_safety_cost_player_window
    ON safety_cost_events (player_scope_tag, recorded_at_ms DESC);
CREATE INDEX idx_safety_cost_npc_window
    ON safety_cost_events (npc_scope_tag, recorded_at_ms DESC);
CREATE INDEX idx_safety_cost_player_npc_window
    ON safety_cost_events (player_npc_scope_tag, recorded_at_ms DESC);

PRAGMA user_version = 2;
