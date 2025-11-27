import os
import sys
from sqlalchemy import create_engine, text

# Add project root to path
sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv()

def migrate():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not set")
        return

    engine = create_engine(db_url)
    
    with engine.begin() as conn:
        print("Adding search_vector column...")
        try:
            conn.execute(text("ALTER TABLE images ADD COLUMN IF NOT EXISTS search_vector tsvector"))
        except Exception as e:
            print(f"Error adding column (might exist): {e}")

        print("Backfilling search_vector...")
        conn.execute(text("UPDATE images SET search_vector = to_tsvector('english', caption) WHERE search_vector IS NULL"))
        
        print("Creating GIN index...")
        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_images_search_vector ON images USING gin(search_vector)"))
        except Exception as e:
            print(f"Error creating index: {e}")
            
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
