"""
Database migration: Add storage fields to images table

This adds the new columns needed for image storage functionality.
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/ai_router")

def migrate():
    """Add storage fields to images table"""
    engine = create_engine(DATABASE_URL)
    
    migrations = [
        "ALTER TABLE images ADD COLUMN IF NOT EXISTS file_path VARCHAR(512);",
        "ALTER TABLE images ADD COLUMN IF NOT EXISTS format VARCHAR(16);",
        "ALTER TABLE images ADD COLUMN IF NOT EXISTS size_bytes INTEGER;",
        "ALTER TABLE images ADD COLUMN IF NOT EXISTS width INTEGER;",
        "ALTER TABLE images ADD COLUMN IF NOT EXISTS height INTEGER;",
        "ALTER TABLE images ADD COLUMN IF NOT EXISTS thumbnail_path VARCHAR(512);",
    ]
    
    print("Running database migration: Add storage fields")
    print("=" * 60)
    
    with engine.begin() as conn:
        for sql in migrations:
            print(f"Executing: {sql}")
            try:
                conn.execute(text(sql))
                print("  ✓ Success")
            except Exception as e:
                print(f"  ✗ Error: {e}")
    
    print("=" * 60)
    print("Migration complete!")
    print("\nNew columns added:")
    print("  - file_path (VARCHAR 512)")
    print("  - format (VARCHAR 16)")
    print("  - size_bytes (INTEGER)")
    print("  - width (INTEGER)")
    print("  - height (INTEGER)")
    print("  - thumbnail_path (VARCHAR 512)")

if __name__ == "__main__":
    migrate()
