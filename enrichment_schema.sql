-- Add column to track AI enrichment status
ALTER TABLE public.temples 
ADD COLUMN IF NOT EXISTS is_ai_enriched boolean DEFAULT false;

-- Add index for performance
CREATE INDEX IF NOT EXISTS idx_temples_is_ai_enriched ON public.temples (is_ai_enriched);
