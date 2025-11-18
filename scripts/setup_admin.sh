#!/bin/bash
# Setup admin profile and backfill existing images

set -e

echo "=========================================="
echo "Phase 1: Create Admin Profile & Backfill"
echo "=========================================="
echo ""

# Generate UUID for admin
ADMIN_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')
ADMIN_EMAIL="admin@imagesearch.local"

echo "Creating admin profile..."
echo "Admin ID: $ADMIN_ID"
echo "Admin Email: $ADMIN_EMAIL"
echo ""

# Create admin profile
docker exec -i infra-postgres-1 psql -U postgres -d ai_router <<EOF
-- Create admin profile
INSERT INTO profiles (id, email, display_name, role, created_at, updated_at)
VALUES ('$ADMIN_ID', '$ADMIN_EMAIL', 'System Administrator', 'admin', NOW(), NOW())
ON CONFLICT (email) DO NOTHING;

-- Show created profile
SELECT id, email, role FROM profiles WHERE email = '$ADMIN_EMAIL';
EOF

echo ""
echo "✓ Admin profile created!"
echo ""

# Count images to migrate
echo "Checking for images to migrate..."
UNOWNED_COUNT=$(docker exec -i infra-postgres-1 psql -U postgres -d ai_router -t -c "SELECT COUNT(*) FROM images WHERE owner_user_id IS NULL;")
UNOWNED_COUNT=$(echo $UNOWNED_COUNT | tr -d ' ')

echo "Found $UNOWNED_COUNT images without owners"
echo ""

if [ "$UNOWNED_COUNT" -gt 0 ]; then
    echo "Backfilling images with admin ownership..."
    
    docker exec -i infra-postgres-1 psql -U postgres -d ai_router <<EOF
-- Backfill existing images
UPDATE images
SET 
    owner_user_id = '$ADMIN_ID',
    visibility = 'public_admin',
    created_at = COALESCE(created_at, NOW()),
    updated_at = NOW()
WHERE owner_user_id IS NULL;

-- Show statistics
SELECT 
    COUNT(*) as total_images,
    COUNT(owner_user_id) as with_owner,
    COUNT(CASE WHEN visibility = 'public_admin' THEN 1 END) as public_admin_images,
    COUNT(CASE WHEN visibility = 'private' THEN 1 END) as private_images,
    COUNT(CASE WHEN visibility = 'public' THEN 1 END) as public_images
FROM images;
EOF
    
    echo ""
    echo "✓ Backfill complete!"
else
    echo "No images to migrate."
fi

echo ""
echo "=========================================="
echo "IMPORTANT: Save this to your .env file"
echo "=========================================="
echo "ADMIN_USER_ID=$ADMIN_ID"
echo ""
echo "Run this command:"
echo "  echo 'ADMIN_USER_ID=$ADMIN_ID' >> .env"
echo ""
echo "=========================================="
echo "Phase 1 Complete! ✓"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Add ADMIN_USER_ID to your .env file (see above)"
echo "2. Proceed to Phase 2: Authentication"
echo ""
