-- Enable UUID extension if not already enabled (standard in Supabase)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create ENUMs for status and role to ensure data integrity
CREATE TYPE lead_status AS ENUM ('new', 'contacted', 'responded', 'booked', 'lost');
CREATE TYPE conversation_role AS ENUM ('user', 'assistant');
CREATE TYPE campaign_status AS ENUM ('active', 'paused', 'completed', 'draft'); -- Assuming some standard statuses for campaigns

-- Table: campaigns
CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    status campaign_status NOT NULL DEFAULT 'draft',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Table: leads
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    phone TEXT NOT NULL,
    name TEXT,
    email TEXT,
    status lead_status NOT NULL DEFAULT 'new',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Table: conversations
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    role conversation_role NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW() -- 'timestamp' renamed to created_at for consistency, or we can keep 'timestamp'
);

-- Indexes
-- Quick search by phone as requested
CREATE INDEX idx_leads_phone ON leads(phone);

-- Index for foreign keys to improve join performance
CREATE INDEX idx_leads_campaign_id ON leads(campaign_id);
CREATE INDEX idx_conversations_lead_id ON conversations(lead_id);

-- Optional: Index for leads status if filtering by status is common
CREATE INDEX idx_leads_status ON leads(status);
