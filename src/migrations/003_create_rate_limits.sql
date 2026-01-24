-- ============================================================
-- Migration 003: Create Rate Limits Table
-- Description: Creates rate_limits table for tracking message sending quotas
-- ============================================================

CREATE TABLE IF NOT EXISTS rate_limits (
    id UUID PRIMARY KEY,
    recipient VARCHAR(255) NOT NULL,
    message_count INTEGER NOT NULL DEFAULT 0,
    window_start BIGINT NOT NULL,
    creation_date BIGINT NOT NULL,
    update_date BIGINT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active'
);

-- Indexes for rate_limits
CREATE INDEX IF NOT EXISTS idx_rate_limits_recipient ON rate_limits(recipient);
CREATE INDEX IF NOT EXISTS idx_rate_limits_window_start ON rate_limits(window_start);
