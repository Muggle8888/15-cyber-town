-- Append-only v9: lossless full permit scopes; transactional rebuild.
CREATE TABLE v9_provider_permits (
    execution_id TEXT PRIMARY KEY
        REFERENCES execution_admissions(execution_id) ON DELETE RESTRICT,
    policy_version TEXT NOT NULL CHECK (policy_version = 'f-009-safety-control-v1'),
    player_scope_tag BLOB NOT NULL CHECK (
        typeof(player_scope_tag) = 'blob' AND length(player_scope_tag) = 32
    ),
    player_npc_scope_tag BLOB NOT NULL CHECK (
        typeof(player_npc_scope_tag) = 'blob' AND length(player_npc_scope_tag) = 32
    ),
    conversation_scope_tag BLOB NOT NULL CHECK (
        typeof(conversation_scope_tag) = 'blob' AND length(conversation_scope_tag) = 32
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

INSERT INTO v9_provider_permits (
    execution_id, policy_version, player_scope_tag, player_npc_scope_tag,
    conversation_scope_tag, acquired_at_ns, released_at_ns, release_reason
)
SELECT execution_id, policy_version,
    CASE WHEN typeof(player_scope_tag) = 'text'
          AND length(player_scope_tag) = 64
          AND player_scope_tag NOT GLOB '*[^0-9a-f]*'
         THEN unhex(player_scope_tag) ELSE NULL END,
    CASE WHEN typeof(player_npc_scope_tag) = 'text'
          AND length(player_npc_scope_tag) = 64
          AND player_npc_scope_tag NOT GLOB '*[^0-9a-f]*'
         THEN unhex(player_npc_scope_tag) ELSE NULL END,
    CASE WHEN typeof(conversation_scope_tag) = 'text'
          AND length(conversation_scope_tag) = 64
          AND conversation_scope_tag NOT GLOB '*[^0-9a-f]*'
         THEN unhex(conversation_scope_tag) ELSE NULL END,
    acquired_at_ns, released_at_ns, release_reason
FROM provider_permits;

DROP TABLE provider_permits;
ALTER TABLE v9_provider_permits RENAME TO provider_permits;

CREATE INDEX provider_permits_active_conversation_idx
ON provider_permits (conversation_scope_tag) WHERE released_at_ns IS NULL;

CREATE INDEX provider_permits_active_player_idx
ON provider_permits (player_scope_tag) WHERE released_at_ns IS NULL;

CREATE INDEX provider_permits_active_player_npc_idx
ON provider_permits (player_npc_scope_tag) WHERE released_at_ns IS NULL;

PRAGMA user_version = 9;
