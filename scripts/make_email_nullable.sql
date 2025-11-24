-- Migration: Make email nullable for CLIENT users
-- Date: 2025-11-19
-- Reason: Clients don't need email (they don't login), only advisors/admins do

-- Make email column nullable
ALTER TABLE usuarios ALTER COLUMN email DROP NOT NULL;

-- Remove unique constraint temporarily
ALTER TABLE usuarios DROP CONSTRAINT IF EXISTS usuarios_email_key;

-- Add conditional unique constraint (only for non-null emails)
CREATE UNIQUE INDEX usuarios_email_unique_idx ON usuarios (email) WHERE email IS NOT NULL;

-- Update existing client users without email to have NULL
UPDATE usuarios 
SET email = NULL 
WHERE rol = 'CLIENT' 
  AND email LIKE '%@teloo.temp';

COMMENT ON COLUMN usuarios.email IS 'Email address - Required for ADVISOR/ADMIN roles, optional for CLIENT role';
