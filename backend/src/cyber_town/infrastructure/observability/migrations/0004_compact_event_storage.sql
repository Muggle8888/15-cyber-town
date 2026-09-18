-- Append-only v4; leaf layout only. Applied inside the repository transaction.
DROP INDEX "idx_trace_stage_events_stage_outcome";

DROP INDEX "idx_trace_stage_events_retention";

DROP INDEX "idx_execution_links_retention";

DROP INDEX "idx_safety_cost_player_window";

DROP INDEX "idx_safety_cost_npc_window";

DROP INDEX "idx_safety_cost_player_npc_window";

CREATE TABLE "v4_trace_stage_events" (
    trace_id TEXT NOT NULL REFERENCES trace_runs (trace_id),
    sequence INTEGER NOT NULL CHECK (sequence BETWEEN 1 AND 14),
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    stage INTEGER NOT NULL CHECK (
        stage IN (
            12, 13, 14,
            15, 16, 17,
            18, 19, 20,
            21, 22, 23,
            24, 25
        )
    ),
    outcome INTEGER NOT NULL CHECK (
        outcome IN (26, 2, 27, 28, 8, 11)
    ),
    reason_code INTEGER NOT NULL CHECK (
        reason_code IN (
            1, 2, 3, 4,
            5, 6, 7, 8,
            9, 10, 11
        )
    ),
    error_code INTEGER NOT NULL CHECK (
        error_code IN (
            1, 29, 30, 31, 32,
            33, 34, 35,
            36, 37
        )
    ),
    started_at_ms INTEGER NOT NULL CHECK (started_at_ms > 0),
    finished_at_ms INTEGER CHECK (finished_at_ms IS NULL OR finished_at_ms >= started_at_ms),
    latency_ms INTEGER NOT NULL CHECK (latency_ms >= 0),
    item_count INTEGER NOT NULL CHECK (item_count >= 0),
    retention_status INTEGER NOT NULL DEFAULT 38 CHECK (retention_status IN (38, 39)),
    PRIMARY KEY (trace_id, sequence),
    UNIQUE (trace_id, stage),
    CHECK (
        (stage = 12 AND sequence = 1)
        OR (stage = 13 AND sequence = 2)
        OR (stage = 14 AND sequence = 3)
        OR (stage = 15 AND sequence = 4)
        OR (stage = 16 AND sequence = 5)
        OR (stage = 17 AND sequence = 6)
        OR (stage = 18 AND sequence = 7)
        OR (stage = 19 AND sequence = 8)
        OR (stage = 20 AND sequence = 9)
        OR (stage = 21 AND sequence = 10)
        OR (stage = 22 AND sequence = 11)
        OR (stage = 23 AND sequence = 12)
        OR (stage = 24 AND sequence = 13)
        OR (stage = 25 AND sequence = 14)
    )
) STRICT, WITHOUT ROWID;

INSERT INTO "v4_trace_stage_events" ("trace_id","sequence","schema_version","stage","outcome","reason_code","error_code","started_at_ms","finished_at_ms","latency_ms","item_count","retention_status") SELECT "trace_id","sequence","schema_version",observability_encode_v1('trace_stage_events','stage',"stage"),observability_encode_v1('trace_stage_events','outcome',"outcome"),observability_encode_v1('trace_stage_events','reason_code',"reason_code"),observability_encode_v1('trace_stage_events','error_code',"error_code"),"started_at_ms","finished_at_ms","latency_ms","item_count",observability_encode_v1('trace_stage_events','retention_status',"retention_status") FROM "trace_stage_events";

DROP TABLE "trace_stage_events";

ALTER TABLE "v4_trace_stage_events" RENAME TO "trace_stage_events";

CREATE TABLE "v4_execution_links" (
    trace_id TEXT PRIMARY KEY REFERENCES trace_runs (trace_id),
    execution_id BLOB NOT NULL CHECK (length(execution_id) = 16),
    link_kind INTEGER NOT NULL CHECK (link_kind IN (40, 41, 42)),
    provider_dispatch_count INTEGER NOT NULL CHECK (provider_dispatch_count IN (0, 1)),
    retention_status INTEGER NOT NULL DEFAULT 38 CHECK (retention_status IN (38, 39)),
    CHECK (
        (link_kind = 40 AND provider_dispatch_count = 1)
        OR (link_kind IN (41, 42) AND provider_dispatch_count = 0)
    )
) STRICT, WITHOUT ROWID;

INSERT INTO "v4_execution_links" ("trace_id","execution_id","link_kind","provider_dispatch_count","retention_status") SELECT "trace_id",observability_encode_v1('execution_links','execution_id',"execution_id"),observability_encode_v1('execution_links','link_kind',"link_kind"),"provider_dispatch_count",observability_encode_v1('execution_links','retention_status',"retention_status") FROM "execution_links";

DROP TABLE "execution_links";

ALTER TABLE "v4_execution_links" RENAME TO "execution_links";

CREATE INDEX idx_execution_links_execution ON execution_links (execution_id, link_kind);

CREATE UNIQUE INDEX idx_execution_links_one_dispatch_owner
    ON execution_links (execution_id) WHERE provider_dispatch_count = 1;

CREATE TABLE "v4_safety_cost_events" (
    trace_id TEXT NOT NULL REFERENCES trace_runs (trace_id),
    execution_id BLOB NOT NULL CHECK (length(execution_id) = 16),
    attempt_number INTEGER NOT NULL CHECK (attempt_number BETWEEN 1 AND 2),
    event_kind INTEGER NOT NULL CHECK (
        event_kind IN (43, 44, 45, 46, 47)
    ),
    policy_version INTEGER NOT NULL CHECK (policy_version = 48),
    pricing_version TEXT NOT NULL CHECK (length(pricing_version) BETWEEN 1 AND 64),
    provider_kind INTEGER NOT NULL CHECK (
        provider_kind IN (49, 50, 51, 52, 53)
    ),
    outcome INTEGER NOT NULL CHECK (
        outcome IN (11, 54, 55, 56, 28)
    ),
    player_scope_tag BLOB NOT NULL CHECK (length(player_scope_tag) = 32),
    npc_scope_tag BLOB NOT NULL CHECK (length(npc_scope_tag) = 32),
    player_npc_scope_tag BLOB NOT NULL CHECK (length(player_npc_scope_tag) = 32),
    reserved_micro_usd INTEGER NOT NULL CHECK (reserved_micro_usd BETWEEN 0 AND 2000),
    actual_cost_micro_usd INTEGER NOT NULL CHECK (
        actual_cost_micro_usd BETWEEN 0 AND reserved_micro_usd
    ),
    prompt_tokens INTEGER NOT NULL CHECK (prompt_tokens BETWEEN 0 AND 32768),
    completion_tokens INTEGER NOT NULL CHECK (completion_tokens BETWEEN 0 AND 256),
    conservative INTEGER NOT NULL CHECK (conservative IN (0, 1)),
    recorded_at_ms INTEGER NOT NULL CHECK (recorded_at_ms > 0),
    PRIMARY KEY (trace_id, attempt_number, event_kind)
) STRICT, WITHOUT ROWID;

INSERT INTO "v4_safety_cost_events" ("trace_id","execution_id","attempt_number","event_kind","policy_version","pricing_version","provider_kind","outcome","player_scope_tag","npc_scope_tag","player_npc_scope_tag","reserved_micro_usd","actual_cost_micro_usd","prompt_tokens","completion_tokens","conservative","recorded_at_ms") SELECT "trace_id",observability_encode_v1('safety_cost_events','execution_id',"execution_id"),"attempt_number",observability_encode_v1('safety_cost_events','event_kind',"event_kind"),observability_encode_v1('safety_cost_events','policy_version',"policy_version"),"pricing_version",observability_encode_v1('safety_cost_events','provider_kind',"provider_kind"),observability_encode_v1('safety_cost_events','outcome',"outcome"),observability_encode_v1('safety_cost_events','player_scope_tag',"player_scope_tag"),observability_encode_v1('safety_cost_events','npc_scope_tag',"npc_scope_tag"),observability_encode_v1('safety_cost_events','player_npc_scope_tag',"player_npc_scope_tag"),"reserved_micro_usd","actual_cost_micro_usd","prompt_tokens","completion_tokens","conservative","recorded_at_ms" FROM "safety_cost_events";

DROP TABLE "safety_cost_events";

ALTER TABLE "v4_safety_cost_events" RENAME TO "safety_cost_events";

CREATE INDEX idx_safety_cost_execution_attempt
    ON safety_cost_events (execution_id, attempt_number, recorded_at_ms);

CREATE TABLE "v4_retry_breaker_events" (
    trace_id TEXT NOT NULL REFERENCES trace_runs(trace_id),
    execution_id BLOB NOT NULL CHECK (length(execution_id) = 16),
    attempt_number INTEGER NOT NULL CHECK (attempt_number BETWEEN 0 AND 2),
    event_kind INTEGER NOT NULL CHECK (event_kind IN (
        57, 58, 59, 60, 61
    )),
    policy_version INTEGER NOT NULL CHECK (policy_version = 62),
    retry_outcome INTEGER NOT NULL CHECK (retry_outcome IN (
        11, 63, 64, 65, 66, 8
    )),
    breaker_state INTEGER NOT NULL CHECK (breaker_state IN (67, 68, 69)),
    breaker_outcome INTEGER NOT NULL CHECK (breaker_outcome IN (
        11, 70, 56, 71, 72, 28
    )),
    failure_reason INTEGER CHECK (failure_reason IS NULL OR failure_reason IN (
        32, 33, 34
    )),
    backoff_ms INTEGER NOT NULL CHECK (backoff_ms BETWEEN 0 AND 400),
    jitter_ms INTEGER NOT NULL CHECK (jitter_ms BETWEEN 0 AND 200),
    deadline_remaining_ms INTEGER NOT NULL CHECK (
        deadline_remaining_ms BETWEEN 0 AND 12000
    ),
    recorded_at_ms INTEGER NOT NULL CHECK (recorded_at_ms > 0),
    PRIMARY KEY (trace_id, attempt_number, event_kind)
) STRICT, WITHOUT ROWID;

INSERT INTO "v4_retry_breaker_events" ("trace_id","execution_id","attempt_number","event_kind","policy_version","retry_outcome","breaker_state","breaker_outcome","failure_reason","backoff_ms","jitter_ms","deadline_remaining_ms","recorded_at_ms") SELECT "trace_id",observability_encode_v1('retry_breaker_events','execution_id',"execution_id"),"attempt_number",observability_encode_v1('retry_breaker_events','event_kind',"event_kind"),observability_encode_v1('retry_breaker_events','policy_version',"policy_version"),observability_encode_v1('retry_breaker_events','retry_outcome',"retry_outcome"),observability_encode_v1('retry_breaker_events','breaker_state',"breaker_state"),observability_encode_v1('retry_breaker_events','breaker_outcome',"breaker_outcome"),observability_encode_v1('retry_breaker_events','failure_reason',"failure_reason"),"backoff_ms","jitter_ms","deadline_remaining_ms","recorded_at_ms" FROM "retry_breaker_events";

DROP TABLE "retry_breaker_events";

ALTER TABLE "v4_retry_breaker_events" RENAME TO "retry_breaker_events";

CREATE INDEX retry_breaker_execution_attempt_idx
ON retry_breaker_events(execution_id, attempt_number, recorded_at_ms);

PRAGMA user_version = 4;
