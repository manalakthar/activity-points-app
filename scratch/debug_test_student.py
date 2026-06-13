import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import get_db, dict_cursor, get_student
from app import resolve_student_mentor

conn = get_db()
cur = dict_cursor(conn)

student_id = '4SO24AI029'
student = get_student(student_id)
print("Student details:", student)

mentor_id, mentor_name = resolve_student_mentor(student)
print(f"Mentor Assigned: {mentor_id} - {mentor_name}")

cur.execute('''
    SELECT COALESCE(SUM(points_awarded), 0) as approved_claimed
    FROM submissions
    WHERE student_id = %s AND year = %s AND status = 'approved'
''', (student_id, student['year']))
approved_claimed = cur.fetchone()['approved_claimed']
print("Approved Claimed points:", approved_claimed)

cur.execute('''
    SELECT * FROM submissions WHERE student_id = %s
''', (student_id,))
subs = cur.fetchall()
print(f"Total submissions for student: {len(subs)}")
for s in subs:
    print(dict(s))

conn.close()
