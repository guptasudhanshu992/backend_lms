# Migration Files - PostgreSQL Compatibility Fix

## Summary
All migration files have been updated to use PostgreSQL-compatible syntax, matching `init_database.py`.

---

## Changes Made

### ✅ 001_create_messages.sql
**Fixed:**
- `INTEGER PRIMARY KEY AUTOINCREMENT` → `SERIAL PRIMARY KEY`
- `DATETIME` → `TIMESTAMP`

### ✅ 002_create_auth_tables.sql
**Fixed:**
- `INTEGER PRIMARY KEY AUTOINCREMENT` → `SERIAL PRIMARY KEY` (all 8 tables)
- `DATETIME` → `TIMESTAMP` (all timestamp columns)
- `BOOLEAN DEFAULT 0` → `BOOLEAN DEFAULT FALSE`
- `BOOLEAN DEFAULT 1` → `BOOLEAN DEFAULT TRUE`
- `INSERT OR IGNORE` → `INSERT ... ON CONFLICT (name) DO NOTHING`

**Tables Updated:**
- users
- roles
- groups
- user_groups
- user_permissions
- sessions
- audit_logs
- password_reset_tokens
- email_verification_tokens

### ✅ 003_create_content_tables.sql
**Fixed:**
- `INTEGER PRIMARY KEY AUTOINCREMENT` → `SERIAL PRIMARY KEY`
- `REAL` → `NUMERIC(10, 2)` for price column
- `DATETIME` → `TIMESTAMP`
- `INTEGER DEFAULT 1` → `BOOLEAN DEFAULT FALSE` for published column
- INSERT values: `1` → `TRUE` for boolean columns
- Added `ON CONFLICT DO NOTHING` to all INSERT statements
- Added `publish_at` and `tags` columns to blogs table (matching init_database.py)

**Tables Updated:**
- courses (now matches init_database.py exactly)
- blogs (now matches init_database.py exactly)

### ✅ 004_add_blog_features.sql
**Fixed:**
- `INTEGER PRIMARY KEY AUTOINCREMENT` → `SERIAL PRIMARY KEY`
- `INSERT OR IGNORE` → `INSERT ... ON CONFLICT (name) DO NOTHING`
- Wrapped ALTER TABLE statements in PostgreSQL DO blocks with IF NOT EXISTS checks
- `TIMESTAMP` instead of `DATETIME`

**Tables Created/Modified:**
- categories (created)
- tags (created)
- blog_tags (created)
- blogs (added publish_at, tags columns with proper checks)

### ✅ 005_fix_audit_logs_columns.sql
**Fixed:**
- Consolidated multiple `DO $$ ... END $$` blocks into single block
- Fixed syntax error: all statements now within one DO block
- Added `RAISE NOTICE` messages for better debugging

**Columns Added to audit_logs:**
- ip (VARCHAR(45))
- user_agent (TEXT)
- status (VARCHAR(50) DEFAULT 'success')
- resource (VARCHAR(255))
- meta (TEXT DEFAULT '{}')
- Renames details → meta if applicable

### ✅ 006_add_price_column_to_courses.sql
**No changes needed** - Already in correct PostgreSQL syntax with proper DO block structure

**Columns Added:**
- users: two_factor_enabled, two_factor_secret, profile_picture, oauth_provider, oauth_provider_id, updated_at
- sessions: refresh_token (renamed from session_token), ip (renamed from ip_address), device_info, last_active_at
- courses: price, updated_at
- blogs: updated_at

---

## Key Syntax Changes

### AUTOINCREMENT → SERIAL
```sql
-- BEFORE (SQLite)
id INTEGER PRIMARY KEY AUTOINCREMENT

-- AFTER (PostgreSQL)
id SERIAL PRIMARY KEY
```

### Boolean Defaults
```sql
-- BEFORE (SQLite uses 0/1)
published INTEGER DEFAULT 1

-- AFTER (PostgreSQL native boolean)
published BOOLEAN DEFAULT TRUE
```

### INSERT OR IGNORE → ON CONFLICT
```sql
-- BEFORE (SQLite)
INSERT OR IGNORE INTO table (col) VALUES ('val');

-- AFTER (PostgreSQL)
INSERT INTO table (col) VALUES ('val')
ON CONFLICT (col) DO NOTHING;
```

### Datetime Types
```sql
-- BEFORE (SQLite)
created_at DATETIME DEFAULT CURRENT_TIMESTAMP

-- AFTER (PostgreSQL)
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

### DO Block Structure
```sql
-- BEFORE (WRONG - split across statements)
DO $$ BEGIN ...
END IF
END $$

-- AFTER (CORRECT - single statement)
DO $$ 
BEGIN
    IF ... THEN
        ...;
    END IF;
END $$;
```

---

## Verification

All migration files now match the table structures in `init_database.py`:
- ✅ Same column names
- ✅ Same data types
- ✅ Same defaults
- ✅ Same constraints
- ✅ PostgreSQL-compatible syntax throughout

---

## Testing

To test migrations on PostgreSQL:
```bash
cd backend
python -m app.db.d1 init
```

To reset database and run all migrations:
```bash
python init_database.py --drop
```

---

## Migration Execution Order

1. ✅ 001_create_messages.sql
2. ✅ 002_create_auth_tables.sql
3. ✅ 003_create_content_tables.sql
4. ✅ 004_add_blog_features.sql
5. ✅ 005_fix_audit_logs_columns.sql
6. ✅ 006_add_price_column_to_courses.sql

All migrations are now idempotent and safe to run multiple times.
