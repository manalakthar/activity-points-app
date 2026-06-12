import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

try:
    print("Adding columns semester and year to submissions table...")
    cur.execute("""
        ALTER TABLE submissions 
        ADD COLUMN IF NOT EXISTS semester INTEGER,
        ADD COLUMN IF NOT EXISTS year INTEGER;
    """)
    conn.commit()
    print("Columns added successfully or already exist!")
except Exception as e:
    conn.rollback()
    print(f"Error adding columns: {e}")

try:
    print("Populating semester and year for existing submissions based on student's current semester/year...")
    cur.execute("""
        UPDATE submissions s
        SET semester = st.semester,
            year = st.year
        FROM students st
        WHERE s.student_id = st.student_id AND (s.semester IS NULL OR s.year IS NULL);
    """)
    conn.commit()
    print("Existing submissions updated successfully!")
except Exception as e:
    conn.rollback()
    print(f"Error updating existing submissions: {e}")

cur.close()
conn.close()
