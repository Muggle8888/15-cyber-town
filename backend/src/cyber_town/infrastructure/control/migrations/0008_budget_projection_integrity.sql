-- Redundant counters detect damage to a derived value without a ledger scan.
-- They are not authentication against a writer able to change both copies.
ALTER TABLE budget_window_totals
    ADD COLUMN checked_attempts_1h INTEGER NOT NULL DEFAULT -1;
ALTER TABLE budget_window_totals
    ADD COLUMN checked_attempts_24h INTEGER NOT NULL DEFAULT -1;
ALTER TABLE budget_window_totals
    ADD COLUMN checked_cost_24h_micro_usd INTEGER NOT NULL DEFAULT -1;

-- The next admission/recovery must rebuild both copies from the ledger.
-- Never legitimize existing projection values by copying them during upgrade.
DELETE FROM budget_window_projection_state;

PRAGMA user_version = 8;
