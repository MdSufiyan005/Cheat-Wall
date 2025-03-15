import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.schema import MetaData, Table, Column
from sqlalchemy.types import Text
import pymysql

# Use PyMySQL as the MySQL driver
pymysql.install_as_MySQLdb()

def update_schema():
    """Update database schema by adding missing columns"""
    try:
        # Get database URL from environment variable
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            print("Error: DATABASE_URL environment variable is not set")
            sys.exit(1)
            
        # Convert PostgreSQL URL to MySQL if needed
        if database_url:
            # Remove PostgreSQL-specific parameters that MySQL doesn't support
            if 'sslmode=' in database_url:
                database_url = database_url.split('?')[0]  # Remove query parameters
                
            # Ensure MySQL dialect is used
            if not database_url.startswith('mysql'):
                if database_url.startswith('postgres://'):
                    database_url = database_url.replace('postgres://', 'mysql://')
                elif database_url.startswith('postgresql://'):
                    database_url = database_url.replace('postgresql://', 'mysql://')
            
        # Create engine
        engine = create_engine(database_url)
        
        # Add whitelisted_processes column to test table if it doesn't exist
        with engine.connect() as conn:
            # Check if column exists - using MySQL information_schema syntax
            result = conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'test' AND column_name = 'whitelisted_processes'"
            ))
            
            if not result.fetchone():
                print("Adding 'whitelisted_processes' column to 'test' table...")
                conn.execute(text(
                    "ALTER TABLE test ADD COLUMN whitelisted_processes TEXT"
                ))
                conn.commit()
                print("Column added successfully")
            else:
                print("Column 'whitelisted_processes' already exists")
                
        print("Database schema update completed")
        
    except Exception as e:
        print(f"Error updating schema: {e}")
        sys.exit(1)
        
if __name__ == "__main__":
    update_schema()