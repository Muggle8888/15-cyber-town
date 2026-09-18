CREATE TABLE budget_window_projection_state (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    projection_version TEXT NOT NULL CHECK (
        projection_version = 'f-009-budget-window-projection-v1'
    ),
    policy_version TEXT NOT NULL CHECK (
        policy_version = 'f-009-budget-policy-v1'
    ),
    hour_cutoff_ns INTEGER NOT NULL CHECK (hour_cutoff_ns > 0),
    day_cutoff_ns INTEGER NOT NULL CHECK (day_cutoff_ns > 0),
    revision INTEGER NOT NULL CHECK (revision >= 1),
    rebuilt_at_ns INTEGER NOT NULL CHECK (rebuilt_at_ns > 0),
    CHECK (hour_cutoff_ns - day_cutoff_ns = 82800000000000)
) STRICT;

CREATE TABLE budget_window_totals (
    scope_class TEXT NOT NULL CHECK (
        scope_class IN ('player_npc', 'player', 'npc', 'global')
    ),
    scope_tag TEXT NOT NULL CHECK (
        length(scope_tag) = 64 AND scope_tag NOT GLOB '*[^0-9a-f]*'
    ),
    attempts_1h INTEGER NOT NULL CHECK (attempts_1h >= 0),
    attempts_24h INTEGER NOT NULL CHECK (attempts_24h >= 0),
    cost_24h_micro_usd INTEGER NOT NULL CHECK (cost_24h_micro_usd >= 0),
    revision INTEGER NOT NULL CHECK (revision >= 1),
    updated_at_ns INTEGER NOT NULL CHECK (updated_at_ns > 0),
    PRIMARY KEY (scope_class, scope_tag),
    CHECK (
        (scope_class = 'global'
            AND scope_tag = '0000000000000000000000000000000000000000000000000000000000000000')
        OR scope_class <> 'global'
    )
) STRICT, WITHOUT ROWID;

PRAGMA user_version = 5;
