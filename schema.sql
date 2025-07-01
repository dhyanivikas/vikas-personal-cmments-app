CREATE TABLE IF NOT EXISTS comments (
    id INT PRIMARY KEY AUTO_INCREMENT NOT NULL,
    text TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- The following UPDATE statement is intended for a one-time migration
-- to set created_at and modified_at for existing records.
-- WARNING: If init_db_schema() in main.py (which executes this script)
-- is run multiple times (e.g., on every application start in development),
-- this will RESET created_at and modified_at for ALL existing records
-- to the current timestamp each time it runs.
-- For a true one-time execution, this should be handled by a dedicated
-- migration script or run manually against the database once.
UPDATE comments SET created_at = CURRENT_TIMESTAMP, modified_at = CURRENT_TIMESTAMP;
