# MySQL to PostgreSQL Migration Guide

This guide walks you through migrating GrantGuard from MySQL to PostgreSQL for cloud deployment on Render.

## Prerequisites

1. PostgreSQL database created on Render (or local PostgreSQL instance)
2. Python 3.8+ installed
3. Access to both MySQL (source) and PostgreSQL (destination) databases

## Step 1: Create PostgreSQL Database on Render

1. Log into Render.com
2. Create a new PostgreSQL database
3. Note the connection details:
   - Host
   - Port (usually 5432)
   - Database name
   - Username
   - Password
   - **DATABASE_URL** (provided by Render in connection info)

## Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 3: Initialize PostgreSQL Schema

Run the PostgreSQL schema file on your Render database:

**Option A: Using psql (recommended)**
```bash
psql $DATABASE_URL < schema_postgresql.sql
```

**Option B: Using Render Dashboard**
- Copy contents of `schema_postgresql.sql`
- Paste into Render's SQL Editor and execute

## Step 4: Migrate Data from MySQL to PostgreSQL

Update environment variables in `migrate_to_postgresql.py` or set them before running:

```bash
# MySQL source (your current database)
export MYSQL_HOST='localhost'
export MYSQL_USER='root'
export MYSQL_PASS='2085965411Pt$'
export MYSQL_DB='grandguard'
export MYSQL_PORT='3306'

# PostgreSQL destination (Render)
export PGHOST='your-render-host'
export PGUSER='your-render-user'
export PGPASSWORD='your-render-password'
export PGDATABASE='your-db-name'
export PGPORT='5432'

# Or use DATABASE_URL
export DATABASE_URL='postgresql://user:pass@host:port/dbname'

# Run migration
python3 migrate_to_postgresql.py
```

## Step 5: Switch Backend to PostgreSQL

1. **Backup your current app.py**:
   ```bash
   cp app.py app_mysql_backup.py
   ```

2. **Replace with PostgreSQL version**:
   ```bash
   cp app_pg.py app.py
   ```

3. **Update environment variables** for PostgreSQL:
   - Set `DATABASE_URL` (Render provides this)
   - Or set `PGHOST`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`, `PGPORT`

## Step 6: Deploy to Render

1. Push your code to GitHub
2. Create a new Web Service on Render
3. Connect your GitHub repository
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `python app.py` (or `gunicorn app:app` for production)
6. Add environment variable:
   - `DATABASE_URL`: Your PostgreSQL connection string from Render
   - `FLASK_SECRET_KEY`: A random secret key for sessions

## Step 7: Verify Migration

Test all functionality:
- [ ] User login
- [ ] User signup
- [ ] Create new grant
- [ ] View dashboard with grants
- [ ] View policies
- [ ] Logout

## Troubleshooting

### Connection Issues
- Verify DATABASE_URL format: `postgresql://user:pass@host:port/dbname`
- Check firewall settings on Render
- Ensure database is accessible from your deployment region

### Data Migration Issues
- Check that all tables were created in PostgreSQL
- Verify row counts match between MySQL and PostgreSQL
- Check for encoding issues (UTF-8 should be default)

### Application Errors
- Check Render logs for detailed error messages
- Verify all environment variables are set
- Ensure `psycopg2-binary` is installed

## Rollback Plan

If you need to rollback:
1. Restore `app_mysql_backup.py` as `app.py`
2. Update DATABASE config to point back to MySQL
3. Restart application

## Notes

- PostgreSQL uses `SERIAL` instead of `AUTO_INCREMENT`
- `ENUM` types in MySQL become `CHECK` constraints in PostgreSQL
- `ON DUPLICATE KEY UPDATE` becomes `ON CONFLICT ... DO UPDATE`
- Dictionary cursors use `RealDictCursor` in psycopg2 instead of `dictionary=True`

