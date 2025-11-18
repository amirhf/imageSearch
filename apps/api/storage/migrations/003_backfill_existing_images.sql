-- Migration 003: Backfill existing images with admin ownership
-- IMPORTANT: Replace '<ADMIN_USER_UUID>' with actual admin UUID before running

-- First, you need to:
-- 1. Create an admin user in your application (sign up)
-- 2. Get the user's UUID from the profiles table
-- 3. Update their role to 'admin'
-- 4. Replace <ADMIN_USER_UUID> below with that UUID

-- Example: Update admin role (run this first with actual email)
-- UPDATE profiles 
-- SET role = 'admin' 
-- WHERE email = 'admin@yourdomain.com';

-- Backfill existing images with admin ownership
-- Replace '<ADMIN_USER_UUID>' with actual UUID from profiles table
UPDATE images
SET 
    owner_user_id = '<ADMIN_USER_UUID>',
    visibility = 'public_admin',
    created_at = COALESCE(created_at, NOW()),
    updated_at = NOW()
WHERE owner_user_id IS NULL;

-- Verify the migration
SELECT 
    COUNT(*) as total_images,
    COUNT(owner_user_id) as owned_images,
    COUNT(CASE WHEN visibility = 'public_admin' THEN 1 END) as public_admin_images,
    COUNT(CASE WHEN visibility = 'private' THEN 1 END) as private_images,
    COUNT(CASE WHEN visibility = 'public' THEN 1 END) as public_images
FROM images;
