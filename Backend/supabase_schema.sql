-- ============================================================
-- ForenSync — Auth Schema (Login + Register only)
-- Paste into Supabase SQL Editor and click Run
-- ============================================================

-- Clean slate
DROP TABLE IF EXISTS users          CASCADE;
DROP TABLE IF EXISTS organizations  CASCADE;
DROP TYPE  IF EXISTS user_role      CASCADE;
DROP TYPE  IF EXISTS user_status    CASCADE;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ────────────────────────────────────────────────────────────
-- 1. ORGANIZATIONS
-- Created on the Register page:
--   • org_name  → "Name" field
--   • org_id    → "Org ID" field  (e.g. ORG-4410)
--   • head_id   → "Organization Head ID" field (e.g. HEAD-XXXX)
-- ────────────────────────────────────────────────────────────
CREATE TABLE organizations (
  id         UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
  org_id     TEXT        NOT NULL UNIQUE,   -- e.g. "ORG-4410"
  name       TEXT        NOT NULL,
  head_id    TEXT        NOT NULL UNIQUE,   -- e.g. "HEAD-0001"
  is_active  BOOLEAN     NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);


-- ────────────────────────────────────────────────────────────
-- 2. USERS  (investigators added during Register)
-- Login page fields:
--   • org_id   → looked up against organizations.org_id
--   • user_id  → matched against users.user_id
--   • role     → toggled in the UI: "head" | "investigator"
-- ────────────────────────────────────────────────────────────
CREATE TYPE user_role   AS ENUM ('head', 'investigator');
CREATE TYPE user_status AS ENUM ('Active', 'Inactive');

CREATE TABLE users (
  id         UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id    TEXT        NOT NULL UNIQUE,   -- e.g. "INV-2291" or "HEAD-0001"
  name       TEXT        NOT NULL,
  role       user_role   NOT NULL DEFAULT 'investigator',
  status     user_status NOT NULL DEFAULT 'Active',
  org_id     UUID        NOT NULL REFERENCES organizations (id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);


-- ────────────────────────────────────────────────────────────
-- INDEXES
-- ────────────────────────────────────────────────────────────
CREATE INDEX idx_users_org_id  ON users (org_id);
CREATE INDEX idx_users_user_id ON users (user_id);


-- ────────────────────────────────────────────────────────────
-- ROW LEVEL SECURITY
-- Open policies for development — lock down after adding JWT auth
-- ────────────────────────────────────────────────────────────
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE users         ENABLE ROW LEVEL SECURITY;

CREATE POLICY "allow_all" ON organizations FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all" ON users         FOR ALL USING (true) WITH CHECK (true);
