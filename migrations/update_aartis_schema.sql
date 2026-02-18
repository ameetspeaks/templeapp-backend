-- Add storage_provider to aartis
ALTER TABLE aartis ADD COLUMN IF NOT EXISTS storage_provider TEXT DEFAULT 'SUPABASE';

-- Ensure other fields exist (idempotent)
ALTER TABLE aartis ADD COLUMN IF NOT EXISTS audio_source_url TEXT;
ALTER TABLE aartis ADD COLUMN IF NOT EXISTS aarti_type TEXT;
ALTER TABLE aartis ADD COLUMN IF NOT EXISTS lyrics_hindi TEXT;
ALTER TABLE aartis ADD COLUMN IF NOT EXISTS lyrics_english_transliteration TEXT;
ALTER TABLE aartis ADD COLUMN IF NOT EXISTS lyrics_english_meaning TEXT;
ALTER TABLE aartis ADD COLUMN IF NOT EXISTS significance TEXT;
ALTER TABLE aartis ADD COLUMN IF NOT EXISTS best_time TEXT;
ALTER TABLE aartis ADD COLUMN IF NOT EXISTS estimated_duration_minutes TEXT;

-- Index for performance
CREATE INDEX IF NOT EXISTS idx_aartis_deity ON aartis(deity);
