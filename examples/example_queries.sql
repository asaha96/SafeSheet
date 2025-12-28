-- Example SQL queries for testing SafeSheet

-- HIGH RISK: UPDATE without WHERE clause
UPDATE users SET status = 'inactive';

-- MEDIUM RISK: UPDATE with WHERE clause
UPDATE users SET status = 'active' WHERE id = 1;

-- HIGH RISK: DELETE without WHERE clause
DELETE FROM orders;

-- MEDIUM RISK: DELETE with WHERE clause
DELETE FROM orders WHERE created_at < '2020-01-01';

-- HIGH RISK: TRUNCATE
TRUNCATE TABLE logs;

-- HIGH RISK: DROP TABLE
DROP TABLE temp_data;

-- HIGH RISK: ALTER TABLE
ALTER TABLE users ADD COLUMN last_login TIMESTAMP;

-- LOW RISK: INSERT
INSERT INTO users (name, email) VALUES ('John Doe', 'john@example.com');

-- LOW RISK: SELECT (read-only)
SELECT * FROM users WHERE status = 'active';

