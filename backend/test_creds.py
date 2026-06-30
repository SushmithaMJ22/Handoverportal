import psycopg2

credentials = [
    ('postgres', 'postgres'),
    ('postgres', 'password'),
    ('postgres', 'root'),
    ('postgres', ''),
    ('user', 'password'),
    ('admin', 'admin'),
]

for user, password in credentials:
    try:
        conn = psycopg2.connect(
            dbname='postgres',
            user=user,
            password=password,
            host='localhost'
        )
        print(f"Success with {user}:{password}")
        conn.close()
        break
    except Exception as e:
        print(f"Failed with {user}:{password}: {e}")
