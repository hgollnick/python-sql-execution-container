-- Create dummy table and insert sample data
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL
);

-- Insert test data
INSERT INTO users (username, email) VALUES
('alice', 'alice@example.com'),
('bob', 'bob@example.com');

-- Create function to sleep for 10 seconds
CREATE OR REPLACE FUNCTION sleep_10_seconds()
RETURNS void AS $$
BEGIN
    PERFORM pg_sleep(10);
END;
$$ LANGUAGE plpgsql;

-- Create view with 10-second delay
CREATE OR REPLACE VIEW users_with_10s_delay AS
SELECT u.*
FROM users u
CROSS JOIN LATERAL sleep_10_seconds();

-- Create function to sleep for 60 seconds
CREATE OR REPLACE FUNCTION sleep_60_seconds()
RETURNS void AS $$
BEGIN
    PERFORM pg_sleep(60);
END;
$$ LANGUAGE plpgsql;

-- Create view with 60-second delay
CREATE OR REPLACE VIEW users_with_60s_delay AS
SELECT u.*
FROM users u
CROSS JOIN LATERAL sleep_60_seconds();
