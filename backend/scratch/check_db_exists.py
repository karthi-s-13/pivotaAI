import psycopg2

try:
    conn = psycopg2.connect("postgresql://postgres:karthikeyan%4013@localhost:5432/portinity")
    print("Connection Successful!")
    cursor = conn.cursor()
    cursor.execute("SELECT current_database();")
    print("Database connected:", cursor.fetchone()[0])
    conn.close()
except Exception as e:
    print("Connection Failed with error:")
    print(e)
    print("Error type:", type(e).__name__)
