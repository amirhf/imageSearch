#!/usr/bin/env python3
"""
Create an admin profile for multi-tenant migration.
This creates a profile directly in the database (without Supabase auth).
For production, you should create the user through Supabase first.
"""
import os
import sys
import uuid
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def create_admin_profile():
    """Create an admin profile in the database"""
    db_url = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/ai_router")
    
    # For Docker, we need to use the host connection
    if "localhost" in db_url:
        print("Note: Using localhost connection. Make sure database is accessible.")
    
    engine = create_engine(db_url)
    
    # Generate a UUID for the admin user
    admin_id = str(uuid.uuid4())
    admin_email = "admin@imagesearch.local"
    
    print("=" * 60)
    print("Creating Admin Profile")
    print("=" * 60)
    print(f"Admin ID: {admin_id}")
    print(f"Admin Email: {admin_email}")
    print()
    
    try:
        with engine.begin() as conn:
            # Check if admin already exists
            result = conn.execute(
                text("SELECT id, email, role FROM profiles WHERE email = :email"),
                {"email": admin_email}
            )
            existing = result.fetchone()
            
            if existing:
                print(f"Admin profile already exists!")
                print(f"ID: {existing[0]}")
                print(f"Email: {existing[1]}")
                print(f"Role: {existing[2]}")
                return str(existing[0])
            
            # Create admin profile
            conn.execute(
                text("""
                    INSERT INTO profiles (id, email, display_name, role, created_at, updated_at)
                    VALUES (:id, :email, :display_name, 'admin', NOW(), NOW())
                """),
                {
                    "id": admin_id,
                    "email": admin_email,
                    "display_name": "System Administrator"
                }
            )
            
            print("✓ Admin profile created successfully!")
            print()
            print("=" * 60)
            print("IMPORTANT: Save this information!")
            print("=" * 60)
            print(f"ADMIN_USER_ID={admin_id}")
            print()
            print("Add this to your .env file:")
            print(f"  echo 'ADMIN_USER_ID={admin_id}' >> .env")
            print()
            
            return admin_id
            
    except Exception as e:
        print(f"ERROR: Failed to create admin profile: {e}")
        sys.exit(1)

def backfill_images(admin_id: str):
    """Backfill existing images with admin ownership"""
    db_url = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/ai_router")
    engine = create_engine(db_url)
    
    print("=" * 60)
    print("Backfilling Existing Images")
    print("=" * 60)
    
    try:
        with engine.begin() as conn:
            # Count images without owner
            result = conn.execute(
                text("SELECT COUNT(*) FROM images WHERE owner_user_id IS NULL")
            )
            unowned_count = result.scalar()
            
            if unowned_count == 0:
                print("No images to migrate. All images already have owners.")
                return
            
            print(f"Found {unowned_count} images without owners")
            print(f"Assigning to admin user: {admin_id}")
            
            # Backfill
            result = conn.execute(
                text("""
                    UPDATE images
                    SET 
                        owner_user_id = :admin_id,
                        visibility = 'public_admin',
                        created_at = COALESCE(created_at, NOW()),
                        updated_at = NOW()
                    WHERE owner_user_id IS NULL
                """),
                {"admin_id": admin_id}
            )
            
            print(f"✓ Updated {result.rowcount} images")
            
            # Verify
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(owner_user_id) as with_owner,
                    COUNT(CASE WHEN visibility = 'public_admin' THEN 1 END) as public_admin,
                    COUNT(CASE WHEN visibility = 'private' THEN 1 END) as private,
                    COUNT(CASE WHEN visibility = 'public' THEN 1 END) as public
                FROM images
            """))
            stats = result.fetchone()
            
            print()
            print("Migration Statistics:")
            print(f"  Total images: {stats[0]}")
            print(f"  With owner: {stats[1]}")
            print(f"  Public admin: {stats[2]}")
            print(f"  Private: {stats[3]}")
            print(f"  Public: {stats[4]}")
            print()
            print("✓ Migration complete!")
            
    except Exception as e:
        print(f"ERROR: Failed to backfill images: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print()
    admin_id = create_admin_profile()
    print()
    
    # Ask user if they want to backfill now
    response = input("Do you want to backfill existing images now? (y/n): ").strip().lower()
    if response == 'y':
        print()
        backfill_images(admin_id)
    else:
        print()
        print("Skipping backfill. You can run it later with:")
        print(f"  ADMIN_USER_ID={admin_id} python scripts/migrate_to_multi_tenant.py")
    
    print()
    print("=" * 60)
    print("Phase 1 Complete!")
    print("=" * 60)
    print("Next steps:")
    print("1. Add ADMIN_USER_ID to your .env file")
    print("2. Proceed to Phase 2: Authentication")
    print()
