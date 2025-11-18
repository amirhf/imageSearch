-- Migration 002: Add multi-tenant fields to images table
-- Adds ownership, visibility, and soft deletion support

-- Add multi-tenant columns to images table
ALTER TABLE images
    ADD COLUMN IF NOT EXISTS owner_user_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS visibility TEXT DEFAULT 'private' CHECK (visibility IN ('private', 'public', 'public_admin')),
    ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_images_owner 
    ON images(owner_user_id) 
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_images_visibility 
    ON images(visibility) 
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_images_deleted 
    ON images(deleted_at);

-- Composite index for common query patterns (owner + visibility)
CREATE INDEX IF NOT EXISTS idx_images_owner_visibility 
    ON images(owner_user_id, visibility) 
    WHERE deleted_at IS NULL;

-- Index for timestamp-based queries
CREATE INDEX IF NOT EXISTS idx_images_created_at 
    ON images(created_at DESC) 
    WHERE deleted_at IS NULL;

-- Add comments for documentation
COMMENT ON COLUMN images.owner_user_id IS 'User who owns this image (NULL for admin-seeded images)';
COMMENT ON COLUMN images.visibility IS 'Access control: private (owner only), public (all users), public_admin (system images)';
COMMENT ON COLUMN images.deleted_at IS 'Soft deletion timestamp (NULL = not deleted)';
