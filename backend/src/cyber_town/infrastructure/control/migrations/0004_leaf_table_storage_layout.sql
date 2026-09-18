-- Append-only v4; leaf layout only. Applied inside the repository transaction.
DROP INDEX "execution_admissions_request_idx";

DROP INDEX "idx_budget_attempt_execution_status";

DROP INDEX "idx_budget_cost_window_time";

DROP INDEX "breaker_results_scope_time_idx";

CREATE TABLE "v4_token_buckets" (
    scope_class TEXT NOT NULL CHECK (
        scope_class IN (
            'ingress_global', 'direct_peer', 'player', 'player_npc', 'conversation'
        )
    ),
    scope_tag TEXT NOT NULL CHECK (
        length(scope_tag) = 64 AND scope_tag NOT GLOB '*[^0-9a-f]*'
    ),
    policy_version TEXT NOT NULL CHECK (policy_version = 'f-009-safety-control-v1'),
    refill_per_minute INTEGER NOT NULL CHECK (refill_per_minute > 0),
    burst_microtokens INTEGER NOT NULL CHECK (burst_microtokens > 0),
    tokens_micro INTEGER NOT NULL CHECK (
        tokens_micro >= 0 AND tokens_micro <= burst_microtokens
    ),
    refill_remainder INTEGER NOT NULL CHECK (
        refill_remainder >= 0 AND refill_remainder < 60000000000
    ),
    last_refill_ns INTEGER NOT NULL CHECK (last_refill_ns > 0),
    PRIMARY KEY (scope_class, scope_tag)
) STRICT, WITHOUT ROWID;

INSERT INTO "v4_token_buckets" ("scope_class","scope_tag","policy_version","refill_per_minute","burst_microtokens","tokens_micro","refill_remainder","last_refill_ns") SELECT "scope_class","scope_tag","policy_version","refill_per_minute","burst_microtokens","tokens_micro","refill_remainder","last_refill_ns" FROM "token_buckets";

DROP TABLE "token_buckets";

ALTER TABLE "v4_token_buckets" RENAME TO "token_buckets";

CREATE TABLE "v4_provider_permits" (
    execution_id TEXT PRIMARY KEY
        REFERENCES execution_admissions(execution_id) ON DELETE RESTRICT,
    policy_version TEXT NOT NULL CHECK (policy_version = 'f-009-safety-control-v1'),
    player_scope_tag TEXT NOT NULL CHECK (
        length(player_scope_tag) = 64 AND player_scope_tag NOT GLOB '*[^0-9a-f]*'
    ),
    player_npc_scope_tag TEXT NOT NULL CHECK (
        length(player_npc_scope_tag) = 64 AND player_npc_scope_tag NOT GLOB '*[^0-9a-f]*'
    ),
    conversation_scope_tag TEXT NOT NULL CHECK (
        length(conversation_scope_tag) = 64
        AND conversation_scope_tag NOT GLOB '*[^0-9a-f]*'
    ),
    acquired_at_ns INTEGER NOT NULL CHECK (acquired_at_ns > 0),
    released_at_ns INTEGER CHECK (
        released_at_ns IS NULL OR released_at_ns >= acquired_at_ns
    ),
    release_reason TEXT CHECK (
        release_reason IS NULL OR release_reason IN (
            'completed', 'cancelled', 'failed', 'control_failure',
            'abandoned_after_restart'
        )
    ),
    CHECK (
        (released_at_ns IS NULL AND release_reason IS NULL)
        OR (released_at_ns IS NOT NULL AND release_reason IS NOT NULL)
    )
) STRICT, WITHOUT ROWID;

INSERT INTO "v4_provider_permits" ("execution_id","policy_version","player_scope_tag","player_npc_scope_tag","conversation_scope_tag","acquired_at_ns","released_at_ns","release_reason") SELECT "execution_id","policy_version","player_scope_tag","player_npc_scope_tag","conversation_scope_tag","acquired_at_ns","released_at_ns","release_reason" FROM "provider_permits";

DROP TABLE "provider_permits";

ALTER TABLE "v4_provider_permits" RENAME TO "provider_permits";

CREATE INDEX provider_permits_active_conversation_idx
ON provider_permits (conversation_scope_tag) WHERE released_at_ns IS NULL;

CREATE INDEX provider_permits_active_player_idx
ON provider_permits (player_scope_tag) WHERE released_at_ns IS NULL;

CREATE INDEX provider_permits_active_player_npc_idx
ON provider_permits (player_npc_scope_tag) WHERE released_at_ns IS NULL;

CREATE TABLE "v4_budget_settlements" (
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
) STRICT, WITHOUT ROWID;

INSERT INTO "v4_budget_settlements" ("execution_id","attempt_number","policy_version","pricing_version","reserved_micro_usd","actual_cost_micro_usd","released_micro_usd","prompt_tokens","completion_tokens","conservative","reason","settled_at_ns") SELECT "execution_id","attempt_number","policy_version","pricing_version","reserved_micro_usd","actual_cost_micro_usd","released_micro_usd","prompt_tokens","completion_tokens","conservative","reason","settled_at_ns" FROM "budget_settlements";

DROP TABLE "budget_settlements";

ALTER TABLE "v4_budget_settlements" RENAME TO "budget_settlements";

CREATE TABLE "v4_breaker_execution_results" (
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
) STRICT, WITHOUT ROWID;

INSERT INTO "v4_breaker_execution_results" ("execution_id","scope_tag","outcome","failure_reason","recorded_at_ns") SELECT "execution_id","scope_tag","outcome","failure_reason","recorded_at_ns" FROM "breaker_execution_results";

DROP TABLE "breaker_execution_results";

ALTER TABLE "v4_breaker_execution_results" RENAME TO "breaker_execution_results";

PRAGMA user_version = 4;
