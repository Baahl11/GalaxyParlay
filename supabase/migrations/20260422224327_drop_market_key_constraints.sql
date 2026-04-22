-- Drop market_key CHECK constraints to allow all market values used by the predictor.
-- The application layer already validates market_key values.
ALTER TABLE model_predictions DROP CONSTRAINT IF EXISTS model_predictions_market_key_check;
ALTER TABLE quality_scores DROP CONSTRAINT IF EXISTS quality_scores_market_key_check;
