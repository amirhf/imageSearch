#!/usr/bin/env python3
"""
Migrate existing Qdrant points to include multi-tenant metadata.
This script syncs Qdrant with PostgreSQL data.
"""
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm
from apps.api.storage.models import ImageDoc
from dotenv import load_dotenv

load_dotenv()

COLLECTION = "images"


def migrate_qdrant_metadata():
    """Sync Qdrant metadata with PostgreSQL"""
    
    print("=" * 60)
    print("Qdrant Multi-Tenant Metadata Migration")
    print("=" * 60)
    print()
    
    # Connect to PostgreSQL
    db_url = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/ai_router")
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    
    # Connect to Qdrant
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_client = QdrantClient(url=qdrant_url)
    
    print(f"PostgreSQL: {db_url}")
    print(f"Qdrant: {qdrant_url}")
    print()
    
    try:
        # Check if collection exists
        try:
            qdrant_client.get_collection(COLLECTION)
            print(f"✓ Qdrant collection '{COLLECTION}' found")
        except Exception as e:
            print(f"✗ Qdrant collection '{COLLECTION}' not found: {e}")
            print("  Please ensure Qdrant is running and the collection exists.")
            return
        
        # Get all images from PostgreSQL
        with Session() as session:
            images = session.query(ImageDoc).all()
            print(f"✓ Found {len(images)} images in PostgreSQL")
            print()
            
            if len(images) == 0:
                print("No images to migrate.")
                return
            
            # Migrate each image
            updated_count = 0
            skipped_count = 0
            error_count = 0
            
            for img in images:
                try:
                    # Check if point exists in Qdrant
                    points = qdrant_client.retrieve(COLLECTION, ids=[img.id])
                    
                    if not points:
                        print(f"  ⚠ Skipping {img.id}: Not found in Qdrant")
                        skipped_count += 1
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
                    qdrant_client.set_payload(
                        collection_name=COLLECTION,
                        payload=updated_payload,
                        points=[img.id]
                    )
                    
                    updated_count += 1
                    
                    if updated_count % 10 == 0:
                        print(f"  Progress: {updated_count}/{len(images)} images updated...")
                    
                except Exception as e:
                    print(f"  ✗ Error updating {img.id}: {e}")
                    error_count += 1
            
            print()
            print("=" * 60)
            print("Migration Complete!")
            print("=" * 60)
            print(f"Updated: {updated_count}")
            print(f"Skipped: {skipped_count}")
            print(f"Errors: {error_count}")
            print()
            
            # Verify a sample
            if updated_count > 0:
                print("Verifying sample point...")
                sample_id = images[0].id
                points = qdrant_client.retrieve(COLLECTION, ids=[sample_id])
                if points:
                    payload = points[0].payload
                    print(f"  Sample ID: {sample_id}")
                    print(f"  Owner: {payload.get('owner_user_id')}")
                    print(f"  Visibility: {payload.get('visibility')}")
                    print(f"  Deleted: {payload.get('deleted_at')}")
                    print("  ✓ Verification successful!")
                print()
    
    except Exception as e:
        print(f"ERROR: Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    migrate_qdrant_metadata()
