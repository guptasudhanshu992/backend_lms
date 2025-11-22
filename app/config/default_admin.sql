-- SQL to create admin user at startup (used by bootstrap script)
INSERT OR IGNORE INTO users (id, email, hashed_password, is_active, is_verified, role)
VALUES (1, 'admin@example.com', '<PLACEHOLDER_HASH>', 1, 1, 'admin');
