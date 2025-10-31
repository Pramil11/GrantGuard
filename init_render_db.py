#!/usr/bin/env python3
"""
Initialize PostgreSQL schema on Render and migrate data from MySQL
"""

import psycopg2
import mysql.connector
from psycopg2.extras import execute_values
import os

# Render PostgreSQL connection
RENDER_DB_URL = "postgresql://admin_user:NXUMDSA8WjBCkn5xBKFkxQGaKGaxNie8@dpg-d426gaje5dus73bfka20-a.oregon-postgres.render.com:5432/grandguard"

# MySQL connection (source)
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '2085965411Pt$',
    'database': 'grandguard',
    'port': 3306
}

def clear_tables(pg_conn):
    """Clear existing data from tables (in reverse dependency order)"""
    print("Clearing existing data...")
    cur = pg_conn.cursor()
    try:
        # Delete in reverse dependency order
        tables = ['llm_responses', 'budget_lines', 'transactions', 'awards', 'policies', 'users']
        for table in tables:
            cur.execute(f"DELETE FROM {table}")
        pg_conn.commit()
        print("✓ Cleared existing data")
    except Exception as e:
        print(f"  Note: {e}")
        pg_conn.rollback()
    finally:
        cur.close()

def init_schema(pg_conn):
    """Initialize PostgreSQL schema"""
    print("Initializing PostgreSQL schema...")
    cur = pg_conn.cursor()
    
    try:
        # Read schema file
        schema_file = os.path.join(os.path.dirname(__file__), "schema_postgresql.sql")
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        # Execute schema (split by semicolons for multiple statements)
        cur.execute(schema_sql)
        pg_conn.commit()
        print("✓ Schema initialized successfully")
    except Exception as e:
        # If tables already exist, that's fine
        if "already exists" in str(e).lower():
            print("  Tables already exist, skipping schema creation")
        else:
            print(f"✗ Schema init error: {e}")
            pg_conn.rollback()
            raise
    finally:
        cur.close()

def migrate_table(mysql_conn, pg_conn, table_name, columns, id_mapping=None):
    """Migrate a single table from MySQL to PostgreSQL"""
    mysql_cur = mysql_conn.cursor(dictionary=True)
    pg_cur = pg_conn.cursor()
    
    try:
        # Fetch all rows from MySQL
        mysql_cur.execute(f"SELECT * FROM `{table_name}`")
        rows = mysql_cur.fetchall()
        
        if not rows:
            print(f"  Table {table_name} is empty, skipping...")
            return 0, {}
        
        # For tables with auto-increment IDs, exclude ID from insert
        # ID column names: user_id, award_id, policy_id, transaction_id, line_id, response_id
        id_col_map = {
            'users': 'user_id',
            'awards': 'award_id',
            'policies': 'policy_id',
            'transactions': 'transaction_id',
            'budget_lines': 'line_id',
            'llm_responses': 'response_id'
        }
        id_col = id_col_map.get(table_name)
        cols_without_id = [c for c in columns if c != id_col] if id_col else columns
        
        # Prepare data, mapping foreign keys if needed
        data_no_id = []
        new_id_mapping = {}
        
        for row in rows:
            old_id = row.get(id_col)
            row_data = []
            
            for col in cols_without_id:
                val = row.get(col)
                
                # Map foreign key IDs if mapping provided
                if id_mapping and col.endswith('_id'):
                    # Map column names to table names for foreign keys
                    fk_map = {
                        'pi_id': 'users',
                        'user_id': 'users',
                        'award_id': 'awards',
                        'transaction_id': 'transactions'
                    }
                    map_key = fk_map.get(col, col.replace('_id', 's'))
                    if val and map_key in id_mapping:
                        val = id_mapping[map_key].get(val)
                
                row_data.append(val)
            
            data_no_id.append(tuple(row_data))
        
        # Insert data
        cols_str = ', '.join(cols_without_id)
        return_col = f"RETURNING {id_col}" if id_col else ""
        
        for i, data_tuple in enumerate(data_no_id):
            old_id = rows[i].get(id_col)
            pg_cur.execute(
                f"INSERT INTO {table_name} ({cols_str}) VALUES ({', '.join(['%s'] * len(cols_without_id))}) {return_col}",
                data_tuple
            )
            if id_col:
                new_id = pg_cur.fetchone()[0] if return_col else None
                if old_id and new_id:
                    new_id_mapping[old_id] = new_id
        
        pg_conn.commit()
        print(f"  ✓ Migrated {len(rows)} rows from {table_name}")
        return len(rows), new_id_mapping
        
    except Exception as e:
        print(f"  ✗ Error migrating {table_name}: {e}")
        pg_conn.rollback()
        return 0, {}
    finally:
        mysql_cur.close()
        pg_cur.close()

def main():
    print("=" * 60)
    print("GrantGuard MySQL to PostgreSQL Migration")
    print("=" * 60)
    
    # Connect to PostgreSQL (Render)
    print("\n[1/3] Connecting to Render PostgreSQL...")
    try:
        pg_conn = psycopg2.connect(RENDER_DB_URL)
        print("✓ Connected to Render PostgreSQL")
    except Exception as e:
        print(f"✗ Failed to connect to PostgreSQL: {e}")
        return
    
    # Connect to MySQL (local)
    print("\n[2/3] Connecting to local MySQL...")
    try:
        mysql_conn = mysql.connector.connect(**MYSQL_CONFIG)
        print("✓ Connected to MySQL")
    except Exception as e:
        print(f"✗ Failed to connect to MySQL: {e}")
        pg_conn.close()
        return
    
    # Initialize schema and migrate data
    print("\n[3/3] Initializing schema and migrating data...")
    try:
        init_schema(pg_conn)
        clear_tables(pg_conn)
        
        # Define table columns (excluding auto-increment IDs for inserts)
        # Order matters: migrate parent tables before child tables (foreign keys)
        tables = [
            ('users', ['name', 'email', 'role', 'password', 'created_at']),
            ('policies', ['policy_level', 'source_name', 'policy_text']),
            ('awards', ['created_by_email', 'title', 'sponsor', 'sponsor_type', 'amount', 
                       'start_date', 'end_date', 'status', 'created_at', 'total_budget', 
                       'pi_id', 'department', 'college', 'contact_email', 'abstract', 
                       'keywords', 'collaborators', 'budget_personnel', 'budget_equipment', 
                       'budget_travel', 'budget_materials']),
            ('transactions', ['award_id', 'user_id', 'category', 'description', 'amount', 
                            'date_submitted', 'status']),
            ('budget_lines', ['award_id', 'category', 'allocated_amount', 'spent_amount']),
            ('llm_responses', ['transaction_id', 'llm_decision', 'reason', 'timestamp'])
        ]
        
        total_rows = 0
        id_mappings = {}
        
        for table_name, columns in tables:
            print(f"\nMigrating {table_name}...")
            
            # Build ID mapping dict for foreign keys
            mapping = {}
            if table_name == 'awards':
                mapping = {'users': id_mappings.get('users', {})}
            elif table_name == 'transactions':
                mapping = {
                    'users': id_mappings.get('users', {}),
                    'awards': id_mappings.get('awards', {})
                }
            elif table_name == 'budget_lines':
                mapping = {'awards': id_mappings.get('awards', {})}
            elif table_name == 'llm_responses':
                mapping = {'transactions': id_mappings.get('transactions', {})}
            
            count, new_mapping = migrate_table(mysql_conn, pg_conn, table_name, columns, mapping)
            total_rows += count
            
            # Store ID mapping for foreign key references
            id_col_map = {
                'users': 'user_id',
                'awards': 'award_id',
                'policies': 'policy_id',
                'transactions': 'transaction_id',
                'budget_lines': 'line_id',
                'llm_responses': 'response_id'
            }
            if table_name in id_col_map and new_mapping:
                id_mappings[table_name] = new_mapping
        
        print("\n" + "=" * 60)
        print(f"✓ Migration completed! {total_rows} total rows migrated")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
    finally:
        mysql_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    main()

