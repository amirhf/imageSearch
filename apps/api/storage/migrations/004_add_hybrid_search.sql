-- Migration 004: Add Hybrid Search Support
-- Adds tsvector column, GIN index, and trigger for automatic updates

-- 1. Add search_vector column
ALTER TABLE images ADD COLUMN IF NOT EXISTS search_vector tsvector;

-- 2. Create GIN index for fast full-text search
CREATE INDEX IF NOT EXISTS images_search_vector_idx ON images USING GIN(search_vector);

-- 3. Create function to update search_vector from caption
CREATE OR REPLACE FUNCTION images_search_vector_update() RETURNS trigger AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', COALESCE(NEW.caption, '')), 'A');
    RETURN NEW;
END
$$ LANGUAGE plpgsql;

-- 4. Create trigger to run on INSERT and UPDATE
DROP TRIGGER IF EXISTS images_search_vector_update ON images;
CREATE TRIGGER images_search_vector_update
    BEFORE INSERT OR UPDATE ON images
    FOR EACH ROW
    EXECUTE FUNCTION images_search_vector_update();

-- 5. Backfill existing data
UPDATE images SET search_vector = setweight(to_tsvector('english', COALESCE(caption, '')), 'A');
