import sqlite3

conn = sqlite3.connect('database.db')
conn.row_factory = sqlite3.Row

# Show all mentors
print("=== MENTORS IN DB ===")
mentors = conn.execute('SELECT * FROM mentors').fetchall()
for m in mentors:
    print(f"  mentor_id={m['mentor_id']}, name={m['name']}, email={m['email']}, dept={m['department']}")

# Show pending submissions and their mentor_id
print("\n=== PENDING SUBMISSIONS ===")
subs = conn.execute("SELECT submission_id, student_id, mentor_id FROM submissions WHERE status='pending'").fetchall()
for s in subs:
    print(f"  sub_id={s['submission_id']}, student={s['student_id']}, mentor_id={s['mentor_id']}")

# Fix: reassign all pending submissions to M009 (the only active mentor)
print("\n=== FIXING: Reassigning pending submissions to M009 ===")
conn.execute("UPDATE submissions SET mentor_id='M009' WHERE status='pending'")
conn.commit()

# Verify
subs = conn.execute("SELECT submission_id, student_id, mentor_id, status FROM submissions WHERE status='pending'").fetchall()
print("After fix:")
for s in subs:
    print(f"  sub_id={s['submission_id']}, student={s['student_id']}, mentor_id={s['mentor_id']}, status={s['status']}")

conn.close()
print("\nDone.")
