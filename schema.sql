-- Liquor Database Schema
-- Drop existing tables if they exist
DROP TABLE IF EXISTS liquor CASCADE;

-- Create liquor table
CREATE TABLE liquor (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    count INTEGER,
    country_of_origin TEXT,
    category_style TEXT,
    region TEXT,
    distillery TEXT,
    age TEXT,
    purchased_approx DATE,
    abv NUMERIC(5, 2),
    volume TEXT,
    price_cost NUMERIC(10, 2),
    opened_closed TEXT,
    errata TEXT,
    replacement_cost NUMERIC(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for common queries
CREATE INDEX idx_liquor_name ON liquor(name);
CREATE INDEX idx_liquor_distillery ON liquor(distillery);
CREATE INDEX idx_liquor_category ON liquor(category_style);
CREATE INDEX idx_liquor_country ON liquor(country_of_origin);
CREATE INDEX idx_liquor_opened_closed ON liquor(opened_closed);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for updated_at
CREATE TRIGGER update_liquor_updated_at BEFORE UPDATE
    ON liquor FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions (adjust as needed)
-- GRANT ALL PRIVILEGES ON TABLE liquor TO your_user;
-- GRANT USAGE, SELECT ON SEQUENCE liquor_id_seq TO your_user;
