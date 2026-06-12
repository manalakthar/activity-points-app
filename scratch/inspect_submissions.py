import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

cur.execute("""
    SELECT s.*, st.semester as student_current_sem, st.year as student_current_year 
    FROM submissions s 
    JOIN students st ON s.student_id = st.student_id
""")
submissions = cur.fetchall()
print(f"Total submissions: {len(submissions)}")
for sub in submissions[:10]:
    print(dict(sub))

cur.close()
conn.close()
