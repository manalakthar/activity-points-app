import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    print("DATABASE_URL environment variable is missing!")
    exit(1)

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

try:
    print("Updating all activities in the activities table...")
    cur.execute("""
        UPDATE activities
        SET max_points_participant = 5,
            max_points_organizer = 10;
    """)
    conn.commit()
    print("✅ All activities updated successfully to Participant: 5, Organizer: 10!")
except Exception as e:
    conn.rollback()
    print(f"❌ Error updating activities: {e}")
finally:
    cur.close()
    conn.close()
