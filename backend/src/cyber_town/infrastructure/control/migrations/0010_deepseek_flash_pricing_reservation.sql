-- Expand the bounded reservation ceiling for the current DeepSeek Flash peak price.
CREATE TABLE "v10_budget_reservations" (
    execution_id TEXT NOT NULL REFERENCES budget_execution_owners (execution_id),
    attempt_number INTEGER NOT NULL CHECK (attempt_number BETWEEN 1 AND 2),
    policy_version TEXT NOT NULL CHECK (policy_version = 'f-009-budget-policy-v1'),
    pricing_version TEXT NOT NULL CHECK (length(pricing_version) BETWEEN 1 AND 64),
    provider_kind TEXT NOT NULL CHECK (
        provider_kind IN ('fake', 'deepseek', 'local-fallback', 'disabled', 'unknown')
    ),
    provider_model TEXT NOT NULL CHECK (length(provider_model) BETWEEN 1 AND 128),
    reserved_micro_usd INTEGER NOT NULL CHECK (
        reserved_micro_usd BETWEEN 0 AND 11000
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

INSERT INTO "v10_budget_reservations" (
    "execution_id","attempt_number","policy_version","pricing_version","provider_kind",
    "provider_model","reserved_micro_usd","soft_warning","status","reserved_at_ns",
    "dispatched_at_ns","settled_at_ns","released_at_ns","release_reason"
) SELECT
    "execution_id","attempt_number","policy_version","pricing_version","provider_kind",
    "provider_model","reserved_micro_usd","soft_warning","status","reserved_at_ns",
    "dispatched_at_ns","settled_at_ns","released_at_ns","release_reason"
FROM "budget_reservations";

CREATE TABLE "v10_budget_settlements" (
    execution_id TEXT NOT NULL,
    attempt_number INTEGER NOT NULL,
    policy_version TEXT NOT NULL CHECK (policy_version = 'f-009-budget-policy-v1'),
    pricing_version TEXT NOT NULL CHECK (length(pricing_version) BETWEEN 1 AND 64),
    reserved_micro_usd INTEGER NOT NULL CHECK (reserved_micro_usd BETWEEN 0 AND 11000),
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
        REFERENCES v10_budget_reservations (execution_id, attempt_number)
) STRICT, WITHOUT ROWID;

INSERT INTO "v10_budget_settlements" (
    "execution_id","attempt_number","policy_version","pricing_version",
    "reserved_micro_usd","actual_cost_micro_usd","released_micro_usd","prompt_tokens",
    "completion_tokens","conservative","reason","settled_at_ns"
) SELECT
    "execution_id","attempt_number","policy_version","pricing_version",
    "reserved_micro_usd","actual_cost_micro_usd","released_micro_usd","prompt_tokens",
    "completion_tokens","conservative","reason","settled_at_ns"
FROM "budget_settlements";

CREATE TABLE "v10_control_execution_intents" (
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
        REFERENCES v10_budget_reservations(execution_id, attempt_number) ON DELETE RESTRICT,
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

INSERT INTO "v10_control_execution_intents" (
    "execution_id","attempt_number","policy_version","state","conservative",
    "created_at_ns","finalized_at_ns","terminal_reason","revision"
) SELECT
    "execution_id","attempt_number","policy_version","state","conservative",
    "created_at_ns","finalized_at_ns","terminal_reason","revision"
FROM "control_execution_intents";

DROP TABLE "control_execution_intents";
DROP TABLE "budget_settlements";
DROP TABLE "budget_reservations";

ALTER TABLE "v10_budget_reservations" RENAME TO "budget_reservations";
ALTER TABLE "v10_budget_settlements" RENAME TO "budget_settlements";
ALTER TABLE "v10_control_execution_intents" RENAME TO "control_execution_intents";

CREATE INDEX idx_budget_attempt_quota_time
    ON budget_reservations (reserved_at_ns DESC, status);

PRAGMA user_version = 10;
