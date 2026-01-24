-- ============================================================
-- Migration 002: Create Message History Tables with Class Table Inheritance
-- Description: Creates base message_history table and channel-specific tables (email, SMS)
-- NOTE: channel_type and status are VARCHAR, Python Enums are used for validation only
-- ============================================================

-- ============================================================
-- BASE MESSAGE HISTORY TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS message_history (
    id UUID PRIMARY KEY,
    template_id UUID NOT NULL,
    template_name VARCHAR(255) NOT NULL,
    recipient VARCHAR(255) NOT NULL,
    channel_type VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    creation_date BIGINT NOT NULL,
    update_date BIGINT NOT NULL,
    CONSTRAINT fk_message_history_template_id 
        FOREIGN KEY (template_id) 
        REFERENCES templates(id)
);

-- Indexes for message_history
CREATE INDEX IF NOT EXISTS idx_message_history_template_id ON message_history(template_id);
CREATE INDEX IF NOT EXISTS idx_message_history_channel_type ON message_history(channel_type);
CREATE INDEX IF NOT EXISTS idx_message_history_recipient ON message_history(recipient);
CREATE INDEX IF NOT EXISTS idx_message_history_status ON message_history(status);
CREATE INDEX IF NOT EXISTS idx_message_history_creation_date ON message_history(creation_date);

-- ============================================================
-- EMAIL MESSAGE HISTORY TABLE (CTI)
-- ============================================================
CREATE TABLE IF NOT EXISTS email_message_history (
    id UUID PRIMARY KEY,
    message_history_id UUID NOT NULL UNIQUE,
    rendered_content TEXT NOT NULL,
    rendered_subject VARCHAR(500) NOT NULL,
    external_message_id VARCHAR(255),
    CONSTRAINT fk_email_message_history_message_history_id 
        FOREIGN KEY (message_history_id) 
        REFERENCES message_history(id) 
        ON DELETE CASCADE
);

-- Index for email_message_history
CREATE UNIQUE INDEX IF NOT EXISTS idx_email_message_history_message_history_id ON email_message_history(message_history_id);

-- ============================================================
-- SMS MESSAGE HISTORY TABLE (CTI)
-- ============================================================
CREATE TABLE IF NOT EXISTS sms_message_history (
    id UUID PRIMARY KEY,
    message_history_id UUID NOT NULL UNIQUE,
    rendered_content TEXT NOT NULL,
    external_message_id VARCHAR(255),
    CONSTRAINT fk_sms_message_history_message_history_id 
        FOREIGN KEY (message_history_id) 
        REFERENCES message_history(id) 
        ON DELETE CASCADE
);

-- Index for sms_message_history
CREATE UNIQUE INDEX IF NOT EXISTS idx_sms_message_history_message_history_id ON sms_message_history(message_history_id);
