-- ============================================================
-- Migration 001: Create Templates Tables with Class Table Inheritance
-- Description: Creates base templates table and channel-specific tables (email, SMS)
-- NOTE: channel_type is VARCHAR, Python Enum is used for validation only
-- ============================================================

-- ============================================================
-- BASE TEMPLATES TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS templates (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    channel_type VARCHAR(20) NOT NULL,
    creation_date BIGINT NOT NULL,
    update_date BIGINT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active'
);

-- Indexes for templates
CREATE UNIQUE INDEX IF NOT EXISTS idx_templates_name ON templates(name);
CREATE INDEX IF NOT EXISTS idx_templates_channel_type ON templates(channel_type);
CREATE INDEX IF NOT EXISTS idx_templates_status ON templates(status);

-- ============================================================
-- EMAIL TEMPLATES TABLE (CTI)
-- ============================================================
CREATE TABLE IF NOT EXISTS email_templates (
    id UUID PRIMARY KEY,
    template_id UUID NOT NULL UNIQUE,
    content TEXT NOT NULL,
    subject VARCHAR(500) NOT NULL,
    CONSTRAINT fk_email_templates_template_id 
        FOREIGN KEY (template_id) 
        REFERENCES templates(id) 
        ON DELETE CASCADE
);

-- Index for email_templates
CREATE UNIQUE INDEX IF NOT EXISTS idx_email_templates_template_id ON email_templates(template_id);

-- ============================================================
-- SMS TEMPLATES TABLE (CTI)
-- ============================================================
CREATE TABLE IF NOT EXISTS sms_templates (
    id UUID PRIMARY KEY,
    template_id UUID NOT NULL UNIQUE,
    content TEXT NOT NULL,
    CONSTRAINT fk_sms_templates_template_id 
        FOREIGN KEY (template_id) 
        REFERENCES templates(id) 
        ON DELETE CASCADE
);

-- Index for sms_templates
CREATE UNIQUE INDEX IF NOT EXISTS idx_sms_templates_template_id ON sms_templates(template_id);
