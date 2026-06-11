import psycopg2
import psycopg2.extras
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get('DATABASE_URL')


def get_db():
    """Connect to Supabase PostgreSQL database."""
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    return conn


def dict_cursor(conn):
    """Return a cursor that gives dict-like rows (access by column name)."""
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


def init_db():
    """
    With Supabase, tables are created by running supabase_schema.sql
    in the Supabase SQL Editor. This function just verifies the connection.
    """
    try:
        conn = get_db()
        cur = dict_cursor(conn)
        cur.execute('SELECT 1')
        conn.close()
        print("[OK] Connected to Supabase successfully!")
    except Exception as e:
        print(f"[ERROR] Could not connect to Supabase: {e}")
        print("Make sure DATABASE_URL is set in your .env file")
        raise


# ============================================================
# STUDENT HELPERS
# ============================================================

def get_student(student_id):
    conn = get_db()
    cur = dict_cursor(conn)
    cur.execute('SELECT * FROM students WHERE student_id = %s', (student_id,))
    student = cur.fetchone()
    conn.close()
    return student


def get_student_by_email(email):
    conn = get_db()
    cur = dict_cursor(conn)
    cur.execute('SELECT * FROM students WHERE email = %s', (email,))
    student = cur.fetchone()
    conn.close()
    return student


def sync_student_total_points(student_id):
    """Recalculate total_points from approved submissions."""
    conn = get_db()
    cur = dict_cursor(conn)

    cur.execute('''
        SELECT COALESCE(SUM(points_awarded), 0) AS total
        FROM submissions
        WHERE student_id = %s AND status = 'approved'
    ''', (student_id,))
    earned = cur.fetchone()['total']

    cur.execute(
        'UPDATE students SET total_points = %s WHERE student_id = %s',
        (earned, student_id)
    )

    cur.execute('SELECT * FROM students WHERE student_id = %s', (student_id,))
    student = cur.fetchone()

    if student['semester'] >= 6 and student['total_points'] < student['points_required']:
        cur.execute(
            'UPDATE students SET watch_list = 1 WHERE student_id = %s',
            (student_id,)
        )
    elif student['total_points'] >= student['points_required']:
        cur.execute(
            'UPDATE students SET watch_list = 0 WHERE student_id = %s',
            (student_id,)
        )

    conn.commit()
    conn.close()
    return earned


# ============================================================
# SUBMISSION HELPERS
# ============================================================

def get_submissions_by_student(student_id):
    conn = get_db()
    cur = dict_cursor(conn)
    cur.execute('''
        SELECT s.*, a.activity_name, a.category
        FROM submissions s
        JOIN activities a ON s.activity_id = a.activity_id
        WHERE s.student_id = %s
        ORDER BY s.submitted_date DESC
    ''', (student_id,))
    submissions = cur.fetchall()
    conn.close()
    return submissions


def get_pending_submissions_for_mentor(mentor_id):
    conn = get_db()
    cur = dict_cursor(conn)
    cur.execute('''
        SELECT s.*, a.activity_name, a.category, st.name AS student_name
        FROM submissions s
        JOIN activities a ON s.activity_id = a.activity_id
        JOIN students st ON s.student_id = st.student_id
        WHERE s.mentor_id = %s AND s.status = 'pending'
        ORDER BY s.submitted_date DESC
    ''', (mentor_id,))
    submissions = cur.fetchall()
    conn.close()
    return submissions


def get_pending_submissions_for_coordinator():
    conn = get_db()
    cur = dict_cursor(conn)
    cur.execute('''
        SELECT s.*, a.activity_name, a.category, st.name AS student_name
        FROM submissions s
        JOIN activities a ON s.activity_id = a.activity_id
        JOIN students st ON s.student_id = st.student_id
        WHERE s.status = 'mentor_approved'
        ORDER BY s.submitted_date DESC
    ''')
    submissions = cur.fetchall()
    conn.close()
    return submissions


def get_pending_submissions_for_college():
    conn = get_db()
    cur = dict_cursor(conn)
    cur.execute('''
        SELECT s.*, a.activity_name, a.category, st.name AS student_name
        FROM submissions s
        JOIN activities a ON s.activity_id = a.activity_id
        JOIN students st ON s.student_id = st.student_id
        WHERE s.status = 'coordinator_approved'
        ORDER BY s.submitted_date DESC
    ''')
    submissions = cur.fetchall()
    conn.close()
    return submissions


# ============================================================
# ACTIVITY HELPERS
# ============================================================

def get_all_activities():
    conn = get_db()
    cur = dict_cursor(conn)
    cur.execute('SELECT * FROM activities ORDER BY category')
    activities = cur.fetchall()
    conn.close()
    return activities


# ============================================================
# MENTOR / ASSIGNMENT HELPERS
# ============================================================

def get_mentor_for_student(student_id, semester):
    conn = get_db()
    cur = dict_cursor(conn)
    cur.execute('''
        SELECT mentor_id FROM mentor_assignments
        WHERE student_id = %s AND semester = %s
        ORDER BY assignment_id DESC
        LIMIT 1
    ''', (student_id, semester))
    assignment = cur.fetchone()
    conn.close()
    return assignment['mentor_id'] if assignment else None


def get_all_assignments():
    conn = get_db()
    cur = dict_cursor(conn)
    cur.execute('''
        SELECT ma.*, s.name AS student_name, m.name AS mentor_name,
               s.department, s.year
        FROM mentor_assignments ma
        JOIN students s ON ma.student_id = s.student_id
        JOIN mentors m ON ma.mentor_id = m.mentor_id
        ORDER BY ma.semester DESC, s.name
    ''')
    assignments = cur.fetchall()
    conn.close()
    return assignments


def get_assignments_for_student(student_id):
    conn = get_db()
    cur = dict_cursor(conn)
    cur.execute('''
        SELECT ma.*, m.name AS mentor_name
        FROM mentor_assignments ma
        JOIN mentors m ON ma.mentor_id = m.mentor_id
        WHERE ma.student_id = %s
        ORDER BY ma.semester
    ''', (student_id,))
    assignments = cur.fetchall()
    conn.close()
    return assignments


# ============================================================
# CALENDAR HELPERS
# ============================================================

def get_current_calendar():
    conn = get_db()
    cur = dict_cursor(conn)
    cur.execute('''
        SELECT * FROM academic_calendar
        WHERE is_current = 1
        ORDER BY calendar_id DESC
        LIMIT 1
    ''')
    calendar = cur.fetchone()
    conn.close()
    return calendar


def get_all_calendars():
    conn = get_db()
    cur = dict_cursor(conn)
    cur.execute('SELECT * FROM academic_calendar ORDER BY calendar_id DESC')
    calendars = cur.fetchall()
    conn.close()
    return calendars


# ============================================================
# ADVANCE SEMESTER HELPERS
# ============================================================

def get_eligible_students(current_semester):
    conn = get_db()
    cur = dict_cursor(conn)
    cur.execute('''
        SELECT * FROM students
        WHERE semester = %s
        AND is_graduated = 0
        AND (
            (student_type = 'regular' AND semester < 8)
            OR
            (student_type = 'lateral' AND semester < 6)
        )
        ORDER BY department, student_id
    ''', (current_semester,))
    students = cur.fetchall()
    conn.close()
    return students


def advance_students(student_ids, academic_year):
    conn = get_db()
    cur = dict_cursor(conn)

    for student_id in student_ids:
        cur.execute('SELECT * FROM students WHERE student_id = %s', (student_id,))
        student = cur.fetchone()
        if not student:
            continue

        current_sem = student['semester']
        current_year = student['year']
        new_sem = current_sem + 1
        new_year = current_year

        if current_sem in [2, 4, 6]:
            new_year = current_year + 1

        is_graduated = 0
        if student['student_type'] == 'regular' and new_sem > 8:
            is_graduated = 1
            new_sem = 8
        elif student['student_type'] == 'lateral' and new_sem > 6:
            is_graduated = 1
            new_sem = 6

        cur.execute('''
            UPDATE students
            SET semester = %s, year = %s, is_graduated = %s
            WHERE student_id = %s
        ''', (new_sem, new_year, is_graduated, student_id))

    conn.commit()
    conn.close()


# ============================================================
# NOTIFICATION HELPERS
# ============================================================

def get_read_notification_keys(user_id, role):
    conn = get_db()
    cur = dict_cursor(conn)
    cur.execute('''
        SELECT notification_key FROM notification_reads
        WHERE user_id = %s AND role = %s
    ''', (user_id, role))
    rows = cur.fetchall()
    conn.close()
    return {row['notification_key'] for row in rows}


def mark_notifications_read(user_id, role, keys):
    if not keys:
        return
    conn = get_db()
    cur = dict_cursor(conn)
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for key in keys:
        cur.execute('''
            INSERT INTO notification_reads
            (user_id, role, notification_key, read_at)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id, role, notification_key)
            DO UPDATE SET read_at = EXCLUDED.read_at
        ''', (user_id, role, key, now))
    conn.commit()
    conn.close()


if __name__ == '__main__':
    init_db()
