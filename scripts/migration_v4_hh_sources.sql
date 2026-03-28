-- Migration v4: Add support for parsing tech from description and title

-- Create new table for tech mentions from different sources
CREATE TABLE IF NOT EXISTS hh_tech_mentions (
    id SERIAL PRIMARY KEY,
    profession VARCHAR(255) NOT NULL,
    technology VARCHAR(255) NOT NULL,
    source VARCHAR(20) NOT NULL, -- 'skills', 'description', 'title'
    vacancy_count INTEGER NOT NULL DEFAULT 0,
    total_vacancies INTEGER NOT NULL DEFAULT 0,
    percentage DECIMAL(5,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(profession, technology, source)
);

CREATE INDEX IF NOT EXISTS idx_hh_tech_profession ON hh_tech_mentions(profession);
CREATE INDEX IF NOT EXISTS idx_hh_tech_source ON hh_tech_mentions(source);
CREATE INDEX IF NOT EXISTS idx_hh_tech_percentage ON hh_tech_mentions(percentage DESC);

-- Migrate existing data from hh_skills to hh_tech_mentions
INSERT INTO hh_tech_mentions (profession, technology, source, vacancy_count, total_vacancies, percentage, updated_at)
SELECT 
    profession, 
    skill as technology, 
    'skills' as source, 
    vacancy_count, 
    total_vacancies, 
    percentage,
    updated_at
FROM hh_skills
ON CONFLICT (profession, technology, source) DO NOTHING;

-- Add trigger for auto-update updated_at
CREATE OR REPLACE FUNCTION update_hh_tech_mentions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_hh_tech_mentions_updated_at ON hh_tech_mentions;
CREATE TRIGGER trigger_hh_tech_mentions_updated_at
    BEFORE UPDATE ON hh_tech_mentions
    FOR EACH ROW
    EXECUTE FUNCTION update_hh_tech_mentions_updated_at();

-- Keep hh_skills for backward compatibility (will be deprecated later)
COMMENT ON TABLE hh_skills IS 'Deprecated: Use hh_tech_mentions instead';
COMMENT ON TABLE hh_tech_mentions IS 'Technology mentions from HH.ru vacancies (skills, description, title)';
