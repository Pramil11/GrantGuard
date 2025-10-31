#!/usr/bin/env python3
"""
Migration script to transfer data from MySQL to PostgreSQL
Run this after setting up your PostgreSQL database on Render
"""

import mysql.connector
import psycopg2
from psycopg2.extras import execute_values
import os
from datetime import datetime

# MySQL connection (source)
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASS', '2085965411Pt$'),
    'database': os.getenv('MYSQL_DB', 'grandguard'),
    'port': int(os.getenv('MYSQL_PORT', '3306'))
}

# PostgreSQL connection (destination) - Update with your Render database URL
POSTGRES_CONFIG = {
    'host': os.getenv('PGHOST', 'localhost'),
    'user': os.getenv('PGUSER', 'postgres'),
    'password': os.getenv('PGPASSWORD', ''),
    'database': os.getenv('PGDATABASE', 'grandguard'),
    'port': int(os.getenv('PGPORT', '5432'))
}

def migrate_table(mysql_conn, pg_conn, table_name, columns):
    """Migrate a single table from MySQL to PostgreSQL"""
    mysql_cur = mysql_conn.cursor(dictionary=True)
    pg_cur = pg_conn.cursor()
    
    try:
        # Fetch all rows from MySQL
        mysql_cur.execute(f"SELECT * FROM `{table_name}`")
        rows = mysql_cur.fetchall()
        
        if not rows:
            print(f"  Table {table_name} is empty, skipping...")
            return
        
        # Convert to list of tuples in column order
        data_tuples = []
        for row in rows:
            # Handle None values and convert enum to string
            tuple_row = tuple(row.get(col, None) for col in columns)
            data_tuples.append(tuple_row)
        
        # Insert into PostgreSQL
        columns_str = ', '.join(columns)
        placeholders = ', '.join(['%s'] * len(columns))
        
        # For tables with SERIAL, exclude the auto-increment column from insert
        id_col = f"{table_name.split('_')[0]}_id"
        if id_col in columns:
            cols_without_id = [c for c in columns if c != id_col]
            cols_str = ', '.join(cols_without_id)
            placeholders_no_id = ', '.join(['%s'] * len(cols_without_id))
            
            # Adjust tuple to exclude ID
            data_no_id = [tuple(row.get(col, None) for col in cols_without_id) for row in rows]
            execute_values(
                pg_cur,
                f"INSERT INTO {table_name} ({cols_str}) VALUES %s",
                data_no_id
            )
        else:
            execute_values(
                pg_cur,
                f"INSERT INTO {table_name} ({columns_str}) VALUES %s",
                data_tuples
            )
        
        pg_conn.commit()
        print(f"  ✓ Migrated {len(rows)} rows from {table_name}")
        
    except Exception as e:
        print(f"  ✗ Error migrating {table_name}: {e}")
        pg_conn.rollback()
    finally:
        mysql_cur.close()
        pg_cur.close()

def main():
    print("Starting MySQL to PostgreSQL migration...")
    
    # Connect to MySQL
    try:
        mysql_conn = mysql.connector.connect(**MYSQL_CONFIG)
        print("✓ Connected to MySQL")
    except Exception as e:
        print(f"✗ Failed to connect to MySQL: {e}")
        return
    
    # Connect to PostgreSQL
    try:
        pg_conn = psycopg2.connect(**POSTGRES_CONFIG)
        print("✓ Connected to PostgreSQL")
    except Exception as e:
        print(f"✗ Failed to connect to PostgreSQL: {e}")
        mysql_conn.close()
        return
    
    # Define table columns (excluding auto-increment IDs for inserts)
    tables = {
        'users': ['name', 'email', 'role', 'password', 'created_at'],
        'awards': ['created_by_email', 'title', 'sponsor', 'sponsor_type', 'amount', 
                   'start_date', 'end_date', 'status', 'created_at', 'total_budget', 
                   'pi_id', 'department', 'college', 'contact_email', 'abstract', 
                   'keywords', 'collaborators', 'budget_personnel', 'budget_equipment', 
                   'budget_travel', 'budget_materials'],
        'policies': ['policy_level', 'source_name', 'policy_text'],
        'transactions': ['award_id', 'user_id', 'category', 'description', 'amount', 
                        'date_submitted', 'status'],
        'budget_lines': ['award_id', 'category', 'allocated_amount', 'spent_amount'],
        'llm_responses': ['transaction_id', 'llm_decision', 'reason', 'timestamp']
    }
    
    # Migrate each table
    for table_name, columns in tables.items():
        print(f"\nMigrating {table_name}...")
        migrate_table(mysql_conn, pg_conn, table_name, columns)
    
    # Close connections
    mysql_conn.close()
    pg_conn.close()
    
    print("\n✓ Migration completed!")

if __name__ == "__main__":
    main()

