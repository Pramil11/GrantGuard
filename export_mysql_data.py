#!/usr/bin/env python3
"""
Export MySQL data to CSV files for backup/manual migration
"""

import mysql.connector
import csv
import os
from datetime import datetime

MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASS', '2085965411Pt$'),
    'database': os.getenv('MYSQL_DB', 'grandguard'),
    'port': int(os.getenv('MYSQL_PORT', '3306'))
}

def export_table(conn, table_name, output_dir):
    """Export a table to CSV"""
    cur = conn.cursor(dictionary=True)
    
    try:
        cur.execute(f"SELECT * FROM `{table_name}`")
        rows = cur.fetchall()
        
        if not rows:
            print(f"  Table {table_name} is empty, skipping...")
            return
        
        csv_path = os.path.join(output_dir, f"{table_name}.csv")
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            if rows:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
        
        print(f"  ✓ Exported {len(rows)} rows from {table_name} to {csv_path}")
        
    except Exception as e:
        print(f"  ✗ Error exporting {table_name}: {e}")
    finally:
        cur.close()

def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"mysql_export_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Exporting MySQL data to {output_dir}/...")
    
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        print("✓ Connected to MySQL")
    except Exception as e:
        print(f"✗ Failed to connect to MySQL: {e}")
        return
    
    tables = ['users', 'awards', 'policies', 'transactions', 'budget_lines', 'llm_responses']
    
    for table in tables:
        print(f"\nExporting {table}...")
        export_table(conn, table, output_dir)
    
    conn.close()
    
    print(f"\n✓ Export completed! Files saved in {output_dir}/")

if __name__ == "__main__":
    main()

