import psycopg2


conn = psycopg2.connect(
    dbname="postgres",
    user="postgres",
    password="admin",
    host="localhost",
    port="5432"
)

conn.autocommit = True
cursor = conn.cursor()

cursor.execute(

    """
    SELECT 1
    FROM pg_database
    WHERE datname = 'physics_rag'
    """
)
exists = cursor.fetchone()

if not exists:
    cursor.execute("CREATE DATABASE physics_rag")
    print("Database created.")
else:
    print("Database already exists.")

cursor.close()
conn.close()