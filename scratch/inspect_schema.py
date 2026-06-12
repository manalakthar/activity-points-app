import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# List tables
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
""")
tables = cur.fetchall()
print("=== TABLES ===")
for t in tables:
    print(t['table_name'])

# Inspect columns of activities, submissions, academic_calendar
for table in ['activities', 'submissions', 'students', 'academic_calendar']:
    print(f"\n=== COLUMNS IN {table} ===")
    cur.execute(f"""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = '{table}'
    """)
    for col in cur.fetchall():
        print(f"  {col['column_name']}: {col['data_type']}")

# Select all rows from academic_calendar
print("\n=== ACADEMIC CALENDAR ===")
cur.execute("SELECT * FROM academic_calendar")
for cal in cur.fetchall():
    print(dict(cal))

# Select all rows from activities
print("\n=== ACTIVITIES ===")
cur.execute("SELECT * FROM activities")
for act in cur.fetchall():
    print(dict(act))

cur.close()
conn.close()
