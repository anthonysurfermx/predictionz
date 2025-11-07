-- Migration to change market IDs from UUID to TEXT
-- This allows us to use Polymarket's hexadecimal condition IDs

-- Step 1: Drop foreign key constraints
ALTER TABLE ai_analysis DROP CONSTRAINT IF EXISTS ai_analysis_market_id_fkey;
ALTER TABLE predictions DROP CONSTRAINT IF EXISTS predictions_market_id_fkey;

-- Step 2: Change column types to TEXT
ALTER TABLE markets ALTER COLUMN id TYPE TEXT;
ALTER TABLE ai_analysis ALTER COLUMN market_id TYPE TEXT;
ALTER TABLE predictions ALTER COLUMN market_id TYPE TEXT;

-- Step 3: Recreate foreign key constraints
ALTER TABLE ai_analysis
  ADD CONSTRAINT ai_analysis_market_id_fkey
  FOREIGN KEY (market_id) REFERENCES markets(id) ON DELETE CASCADE;

ALTER TABLE predictions
  ADD CONSTRAINT predictions_market_id_fkey
  FOREIGN KEY (market_id) REFERENCES markets(id) ON DELETE CASCADE;

-- Step 4: Remove default UUID generation if it exists
ALTER TABLE markets ALTER COLUMN id DROP DEFAULT;
ALTER TABLE ai_analysis ALTER COLUMN market_id DROP DEFAULT;
ALTER TABLE predictions ALTER COLUMN market_id DROP DEFAULT;
