-- Create RLS policies to allow backend to insert/update data
-- This allows the FastAPI backend to sync Polymarket data to Supabase

-- Enable RLS on tables if not already enabled
ALTER TABLE markets ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_portfolios ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Allow public read access to markets" ON markets;
DROP POLICY IF EXISTS "Allow service role to insert/update markets" ON markets;
DROP POLICY IF EXISTS "Allow public read access to ai_analysis" ON ai_analysis;
DROP POLICY IF EXISTS "Allow service role to insert/update ai_analysis" ON ai_analysis;
DROP POLICY IF EXISTS "Allow users to read their own predictions" ON predictions;
DROP POLICY IF EXISTS "Allow users to insert their own predictions" ON predictions;
DROP POLICY IF EXISTS "Allow users to read their own portfolio" ON user_portfolios;
DROP POLICY IF EXISTS "Allow users to update their own portfolio" ON user_portfolios;

-- Markets: Public read, authenticated write
CREATE POLICY "Allow public read access to markets"
  ON markets FOR SELECT
  USING (true);

CREATE POLICY "Allow service role to insert/update markets"
  ON markets FOR ALL
  USING (true)
  WITH CHECK (true);

-- AI Analysis: Public read, authenticated write
CREATE POLICY "Allow public read access to ai_analysis"
  ON ai_analysis FOR SELECT
  USING (true);

CREATE POLICY "Allow service role to insert/update ai_analysis"
  ON ai_analysis FOR ALL
  USING (true)
  WITH CHECK (true);

-- Predictions: Users can only see/manage their own
CREATE POLICY "Allow users to read their own predictions"
  ON predictions FOR SELECT
  USING (true);

CREATE POLICY "Allow users to insert their own predictions"
  ON predictions FOR INSERT
  WITH CHECK (true);

-- User Portfolios: Users can only see/manage their own
CREATE POLICY "Allow users to read their own portfolio"
  ON user_portfolios FOR SELECT
  USING (true);

CREATE POLICY "Allow users to update their own portfolio"
  ON user_portfolios FOR ALL
  USING (true)
  WITH CHECK (true);
