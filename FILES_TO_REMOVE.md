# Files No Longer Needed After PostgreSQL Migration

## Files You Can Delete (One-time Migration Scripts):

1. **`migrate_to_postgresql.py`** - One-time migration script (already completed)
2. **`init_render_db.py`** - One-time migration script (already completed)
3. **`export_mysql_data.py`** - Optional backup script (if you don't need CSV exports)

## Files You Can Keep or Remove:

### Keep (Recommended):
- **`app_mysql_backup.py`** - Backup of old MySQL version (good for reference/rollback)
- **`schema.sql`** - Old MySQL schema (you mentioned it's not used, but good to keep for reference)
- **`schema_postgresql.sql`** - **KEEP** - Current PostgreSQL schema (needed)
- **`MIGRATION_GUIDE.md`** - **KEEP** - Documentation (useful reference)

### Remove (Optional):
- **`app_pg.py`** - No longer needed (was copied to `app.py`)
  - You already have `app.py` using PostgreSQL
  - You have `app_mysql_backup.py` as backup

## Files Currently Active:
- ✅ **`app.py`** - Active PostgreSQL backend
- ✅ **`requirements.txt`** - Contains psycopg2-binary (PostgreSQL driver)
- ✅ **`schema_postgresql.sql`** - PostgreSQL schema definition

