#!/usr/bin/env python3
"""
Complete migration script for multi-tenant implementation.
Migrates both PostgreSQL and Qdrant data.
"""
import os
import sys
import argparse
from datetime import datetime
from typing import Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from qdrant_client import QdrantClient
from apps.api.storage.models import ImageDoc, Profile
from dotenv import load_dotenv

load_dotenv()

ADMIN_USER_ID = os.getenv("ADMIN_USER_ID", "0ed886d9-622f-4585-a36d-bc082c09acba")
QDRANT_COLLECTION = "images"


class MultiTenantMigration:
    def __init__(self):
        # Database connection
        db_url = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/ai_router")
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        
        # Qdrant connection
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.qdrant_client = QdrantClient(url=qdrant_url)
        
        self.stats = {
            "profiles_created": 0,
            "images_updated": 0,
            "qdrant_updated": 0,
            "errors": 0
        }
    
    def print_header(self, title: str):
        """Print a formatted header"""
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70 + "\n")
    
    def check_prerequisites(self) -> bool:
        """Check if prerequisites are met"""
        self.print_header("Checking Prerequisites")
        
        try:
            # Check database connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("✓ Database connection successful")
            
            # Check if profiles table exists
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'profiles'
                    )
                """))
                if not result.scalar():
                    print("✗ Profiles table does not exist. Run migrations first.")
                    return False
            print("✓ Profiles table exists")
            
            # Check if images table has multi-tenant columns
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'images' 
                    AND column_name IN ('owner_user_id', 'visibility', 'deleted_at')
                """))
                columns = [row[0] for row in result]
                if len(columns) < 3:
                    print(f"✗ Images table missing columns: {set(['owner_user_id', 'visibility', 'deleted_at']) - set(columns)}")
                    return False
            print("✓ Images table has multi-tenant columns")
            
            # Check Qdrant connection
            try:
                self.qdrant_client.get_collection(QDRANT_COLLECTION)
                print("✓ Qdrant connection successful")
            except Exception as e:
                print(f"⚠ Qdrant collection not found: {e}")
                print("  (This is OK if you're using PgVector only)")
            
            return True
            
        except Exception as e:
            print(f"✗ Error checking prerequisites: {e}")
            return False
    
    def create_admin_profile(self) -> bool:
        """Create admin profile if it doesn't exist"""
        self.print_header("Creating Admin Profile")
        
        try:
            with self.Session() as session:
                # Check if admin profile exists
                admin = session.query(Profile).filter_by(id=ADMIN_USER_ID).first()
                
                if admin:
                    print(f"✓ Admin profile already exists: {admin.email}")
                    return True
                
                # Create admin profile
                admin = Profile(
                    id=ADMIN_USER_ID,
                    email="admin@example.com",
                    role="admin"
                )
                session.add(admin)
                session.commit()
                
                self.stats["profiles_created"] += 1
                print(f"✓ Created admin profile: {admin.email}")
                return True
                
        except Exception as e:
            print(f"✗ Error creating admin profile: {e}")
            return False
    
    def migrate_database_images(self) -> bool:
        """Migrate existing images in database"""
        self.print_header("Migrating Database Images")
        
        try:
            with self.Session() as session:
                # Get images without owner
                images = session.query(ImageDoc).filter(
                    ImageDoc.owner_user_id == None
                ).all()
                
                if not images:
                    print("✓ No images to migrate (all have owners)")
                    return True
                
                print(f"Found {len(images)} images without owners")
                
                # Update images
                for i, img in enumerate(images, 1):
                    img.owner_user_id = ADMIN_USER_ID
                    img.visibility = "public_admin"
                    
                    if not img.created_at:
                        img.created_at = datetime.utcnow()
                    if not img.updated_at:
                        img.updated_at = datetime.utcnow()
                    
                    self.stats["images_updated"] += 1
                    
                    if i % 10 == 0:
                        print(f"  Progress: {i}/{len(images)} images updated...")
                
                session.commit()
                print(f"✓ Updated {self.stats['images_updated']} images")
                return True
                
        except Exception as e:
            print(f"✗ Error migrating database images: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def migrate_qdrant_metadata(self) -> bool:
        """Migrate Qdrant metadata"""
        self.print_header("Migrating Qdrant Metadata")
        
        try:
            # Check if collection exists
            try:
                self.qdrant_client.get_collection(QDRANT_COLLECTION)
            except Exception:
                print("⚠ Qdrant collection not found, skipping Qdrant migration")
                return True
            
            with self.Session() as session:
                # Get all images from database
                images = session.query(ImageDoc).all()
                
                if not images:
                    print("✓ No images to sync to Qdrant")
                    return True
                
                print(f"Found {len(images)} images to sync")
                
                # Update Qdrant points
                for i, img in enumerate(images, 1):
                    try:
                        # Check if point exists in Qdrant
                        points = self.qdrant_client.retrieve(
                            collection_name=QDRANT_COLLECTION,
                            ids=[img.id]
                        )
                        
                        if not points:
                            print(f"  ⚠ Skipping {img.id}: Not found in Qdrant")
                            continue
                        
                        # Get existing payload
                        existing_payload = points[0].payload or {}
                        
                        # Update with multi-tenant fields
                        updated_payload = {
                            **existing_payload,
                            "owner_user_id": str(img.owner_user_id) if img.owner_user_id else None,
                            "visibility": img.visibility or "private",
                            "deleted_at": img.deleted_at.isoformat() if img.deleted_at else None,
                            "created_at": img.created_at.isoformat() if img.created_at else datetime.utcnow().isoformat(),
                            "updated_at": img.updated_at.isoformat() if img.updated_at else datetime.utcnow().isoformat(),
                        }
                        
                        # Update Qdrant point
                        self.qdrant_client.set_payload(
                            collection_name=QDRANT_COLLECTION,
                            payload=updated_payload,
                            points=[img.id]
                        )
                        
                        self.stats["qdrant_updated"] += 1
                        
                        if i % 10 == 0:
                            print(f"  Progress: {i}/{len(images)} points updated...")
                        
                    except Exception as e:
                        print(f"  ✗ Error updating {img.id}: {e}")
                        self.stats["errors"] += 1
                
                print(f"✓ Updated {self.stats['qdrant_updated']} Qdrant points")
                return True
                
        except Exception as e:
            print(f"✗ Error migrating Qdrant metadata: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def verify_migration(self) -> bool:
        """Verify migration was successful"""
        self.print_header("Verifying Migration")
        
        try:
            with self.Session() as session:
                # Check images without owners
                orphan_count = session.query(ImageDoc).filter(
                    ImageDoc.owner_user_id == None
                ).count()
                
                if orphan_count > 0:
                    print(f"⚠ Warning: {orphan_count} images still without owners")
                else:
                    print("✓ All images have owners")
                
                # Check visibility distribution
                result = session.execute(text("""
                    SELECT visibility, COUNT(*) 
                    FROM images 
                    GROUP BY visibility
                """))
                
                print("\nVisibility distribution:")
                for row in result:
                    print(f"  {row[0] or 'NULL'}: {row[1]} images")
                
                # Sample verification
                sample = session.query(ImageDoc).first()
                if sample:
                    print(f"\nSample image verification:")
                    print(f"  ID: {sample.id}")
                    print(f"  Owner: {sample.owner_user_id}")
                    print(f"  Visibility: {sample.visibility}")
                    print(f"  Deleted: {sample.deleted_at}")
                
                return orphan_count == 0
                
        except Exception as e:
            print(f"✗ Error verifying migration: {e}")
            return False
    
    def print_summary(self):
        """Print migration summary"""
        self.print_header("Migration Summary")
        
        print(f"Profiles created:    {self.stats['profiles_created']}")
        print(f"Database images:     {self.stats['images_updated']}")
        print(f"Qdrant points:       {self.stats['qdrant_updated']}")
        print(f"Errors:              {self.stats['errors']}")
        print()
        
        if self.stats['errors'] == 0:
            print("✓ Migration completed successfully!")
        else:
            print(f"⚠ Migration completed with {self.stats['errors']} errors")
    
    def run(self, auto_confirm=False):
        """Run the complete migration"""
        print("\n" + "=" * 70)
        print("  MULTI-TENANT MIGRATION")
        print("  This script will migrate existing data to multi-tenant schema")
        print("=" * 70)
        
        # Check prerequisites
        if not self.check_prerequisites():
            print("\n✗ Prerequisites not met. Please fix issues and try again.")
            return False
        
        # Confirm before proceeding
        print("\nThis will:")
        print("  1. Create admin profile (if needed)")
        print("  2. Assign all existing images to admin user")
        print("  3. Set visibility to 'public_admin' for existing images")
        print("  4. Update Qdrant metadata")
        print()
        
        if not auto_confirm:
            response = input("Continue with migration? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("Migration cancelled.")
                return False
        else:
            print("Auto-confirm enabled, proceeding with migration...")
        
        # Run migration steps
        success = True
        success = success and self.create_admin_profile()
        success = success and self.migrate_database_images()
        success = success and self.migrate_qdrant_metadata()
        success = success and self.verify_migration()
        
        # Print summary
        self.print_summary()
        
        return success


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Migrate to multi-tenant schema')
    parser.add_argument('--yes', '-y', action='store_true', 
                        help='Auto-confirm migration without prompting')
    args = parser.parse_args()
    
    migration = MultiTenantMigration()
    success = migration.run(auto_confirm=args.yes)
    sys.exit(0 if success else 1)
