CREATE TABLE token_buckets (
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
) STRICT;

CREATE TABLE execution_admissions (
    execution_id TEXT PRIMARY KEY CHECK (length(execution_id) = 36),
    request_id TEXT NOT NULL CHECK (length(request_id) = 36),
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
    admitted_at_ns INTEGER NOT NULL CHECK (admitted_at_ns > 0)
) STRICT;

CREATE INDEX execution_admissions_request_idx
ON execution_admissions (request_id, admitted_at_ns);

CREATE TABLE provider_permits (
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
) STRICT;

CREATE INDEX provider_permits_active_player_idx
ON provider_permits (player_scope_tag) WHERE released_at_ns IS NULL;

CREATE INDEX provider_permits_active_player_npc_idx
ON provider_permits (player_npc_scope_tag) WHERE released_at_ns IS NULL;

CREATE INDEX provider_permits_active_conversation_idx
ON provider_permits (conversation_scope_tag) WHERE released_at_ns IS NULL;

PRAGMA user_version = 1;
