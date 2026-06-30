import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_db():
    try:
        # Connect to default postgres database to create the new one
        conn = psycopg2.connect(
            dbname='postgres',
            user='postgres',
            password='password', # Trying common local password
            host='localhost'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Check if db exists
        cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'handoverdb'")
        exists = cur.fetchone()
        if not exists:
            cur.execute('CREATE DATABASE handoverdb')
            print("Database handoverdb created successfully")
        else:
            print("Database handoverdb already exists")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
        # Try without password
        try:
            conn = psycopg2.connect(
                dbname='postgres',
                user='postgres',
                host='localhost'
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'handoverdb'")
            exists = cur.fetchone()
            if not exists:
                cur.execute('CREATE DATABASE handoverdb')
                print("Database handoverdb created successfully (no password)")
            else:
                print("Database handoverdb already exists")
            cur.close()
            conn.close()
        except Exception as e2:
            print(f"Error without password: {e2}")

if __name__ == "__main__":
    create_db()
