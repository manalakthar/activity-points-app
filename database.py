import sqlite3
from datetime import datetime

DATABASE = 'database.db'

def get_db():
    """Connect to the database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create all tables if they don't exist."""
    conn = get_db()
    cursor = conn.cursor()

    # Students table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            department TEXT NOT NULL,
            year INTEGER NOT NULL,
            semester INTEGER NOT NULL,
            student_type TEXT DEFAULT 'regular',
            points_required INTEGER DEFAULT 100,
            total_points INTEGER DEFAULT 0,
            watch_list INTEGER DEFAULT 0,
            face_photo_path TEXT
        )
    ''')

    # Faculty mentors table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mentors (
            mentor_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            department TEXT NOT NULL
        )
    ''')

    # Coordinators table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS coordinators (
            coordinator_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            department TEXT
        )
    ''')

    # Academic calendar table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS academic_calendar (
            calendar_id INTEGER PRIMARY KEY AUTOINCREMENT,
            semester INTEGER NOT NULL,
            academic_year TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            is_current INTEGER DEFAULT 0,
            created_at TEXT
        )
    ''')
    # Add is_current column if it doesn't exist
    try:
        cursor.execute('''
            ALTER TABLE students ADD COLUMN is_graduated INTEGER DEFAULT 0
        ''')
    except:
        pass
    # Admin table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            admin_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # Mentor assignments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mentor_assignments (
            assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            mentor_id TEXT NOT NULL,
            semester INTEGER NOT NULL,
            academic_year TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students (student_id),
            FOREIGN KEY (mentor_id) REFERENCES mentors (mentor_id)
        )
    ''')

    # Add default admin account
    try:
        cursor.execute('''
            INSERT INTO admins (admin_id, name, email, password)
            VALUES (?, ?, ?, ?)
        ''', ('ADMIN001', 'SJEC Admin', 'admin@sjec.ac.in', 'admin123'))
    except:
        pass  # Admin already exists

    # Activities table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            activity_name TEXT NOT NULL,
            min_duration_hours INTEGER NOT NULL,
            max_points_participant INTEGER NOT NULL,
            max_points_organizer INTEGER NOT NULL
        )
    ''')

    # Submissions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            submission_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            activity_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            organized_by TEXT NOT NULL,
            activity_date TEXT NOT NULL,
            duration_hours INTEGER NOT NULL,
            points_claimed INTEGER NOT NULL,
            points_awarded INTEGER DEFAULT 0,
            certificate_path TEXT,
            extracted_text TEXT,
            face_matched INTEGER DEFAULT 0,
            protsaha_updated INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            mentor_id TEXT,
            submitted_date TEXT,
            reviewed_date TEXT,
            rejection_note TEXT,
            FOREIGN KEY (student_id) REFERENCES students (student_id),
            FOREIGN KEY (activity_id) REFERENCES activities (activity_id)
        )
    ''')
    # Add rejection_note column if it doesn't exist
    try:
        cursor.execute('''
            ALTER TABLE submissions ADD COLUMN rejection_note TEXT
        ''')
    except:
        pass  # Column already exists

    # Pre-fill activities table with all activities from the policy
    cursor.execute("SELECT COUNT(*) FROM activities")
    count = cursor.fetchone()[0]

    if count == 0:
        activities = [
            # Societal & Community
            ('Societal & Community', 'NGO Volunteering', 6, 10, 20),
            ('Societal & Community', 'Blood Donation Camp', 6, 10, 20),
            ('Societal & Community', 'Tree Plantation Drive', 6, 10, 20),
            ('Societal & Community', 'Village Survey Project', 6, 10, 20),
            ('Societal & Community', 'Swachh Bharat Initiative', 6, 10, 20),
            ('Societal & Community', 'Rural Outreach Program', 6, 10, 20),

            # Technical & Innovation
            ('Technical & Innovation', 'Hackathon/Ideathon', 8, 10, 20),
            ('Technical & Innovation', 'Internship/Industrial Training', 8, 10, 20),
            ('Technical & Innovation', 'Technical Paper Publication', 8, 10, 20),
            ('Technical & Innovation', 'Patent/Copyright Filing', 8, 10, 20),
            ('Technical & Innovation', 'Prototype Development', 8, 10, 20),
            ('Technical & Innovation', 'Project Expo', 8, 10, 20),

            # Leadership & Professional
            ('Leadership & Professional', 'College Club Position', 0, 5, 10),
            ('Leadership & Professional', 'Class Representative', 0, 5, 10),
            ('Leadership & Professional', 'Tech Fest/Workshop Organization', 0, 5, 10),
            ('Leadership & Professional', 'IEEE/ISTE Membership', 0, 5, 10),
            ('Leadership & Professional', 'NCC/NSS Activities', 0, 5, 10),
            ('Leadership & Professional', 'Online Course (NPTEL/Coursera)', 0, 10, 10),
            ('Leadership & Professional', 'Certification Achievement', 0, 10, 10),

            # Sports, Arts & Wellness
            ('Sports, Arts & Wellness', 'VTU/State Level Sports', 0, 5, 10),
            ('Sports, Arts & Wellness', 'Intra-college Sports/Cultural', 0, 5, 10),
            ('Sports, Arts & Wellness', 'Yoga/Mental Health Workshop', 0, 5, 10),
            ('Sports, Arts & Wellness', 'Green Initiative Activity', 0, 5, 10),

            # Special/National Initiatives
            ('Special/National Initiatives', 'NISP Implementation', 0, 5, 10),
            ('Special/National Initiatives', 'Entrepreneurship Activity', 0, 5, 10),
            ('Special/National Initiatives', 'Other Approved Activity', 0, 5, 10),
        ]

        cursor.executemany('''
            INSERT INTO activities 
            (category, activity_name, min_duration_hours, 
             max_points_participant, max_points_organizer)
            VALUES (?, ?, ?, ?, ?)
        ''', activities)

    conn.commit()
    conn.close()
    print("[OK] Database initialized successfully!")
    print("[OK] All tables created!")
    print("[OK] Activities pre-loaded!")

# Helper functions for students
def get_student(student_id):
    conn = get_db()
    student = conn.execute(
        'SELECT * FROM students WHERE student_id = ?', 
        (student_id,)
    ).fetchone()
    conn.close()
    return student

def get_student_by_email(email):
    conn = get_db()
    student = conn.execute(
        'SELECT * FROM students WHERE email = ?', 
        (email,)
    ).fetchone()
    conn.close()
    return student

def update_student_points(student_id, points_to_add):
    conn = get_db()
    conn.execute('''
        UPDATE students 
        SET total_points = total_points + ?
        WHERE student_id = ?
    ''', (points_to_add, student_id))

    # Auto flag watch list if semester 6 and below required points
    student = conn.execute(
        'SELECT * FROM students WHERE student_id = ?',
        (student_id,)
    ).fetchone()

    if student['semester'] >= 6 and student['total_points'] < student['points_required']:
        conn.execute(
            'UPDATE students SET watch_list = 1 WHERE student_id = ?',
            (student_id,)
        )

    conn.commit()
    conn.close()

# Helper functions for submissions
def get_submissions_by_student(student_id):
    conn = get_db()
    submissions = conn.execute('''
        SELECT s.*, a.activity_name, a.category 
        FROM submissions s
        JOIN activities a ON s.activity_id = a.activity_id
        WHERE s.student_id = ?
        ORDER BY s.submitted_date DESC
    ''', (student_id,)).fetchall()
    conn.close()
    return submissions

def get_pending_submissions_for_mentor(mentor_id):
    conn = get_db()
    submissions = conn.execute('''
        SELECT s.*, a.activity_name, a.category, st.name as student_name
        FROM submissions s
        JOIN activities a ON s.activity_id = a.activity_id
        JOIN students st ON s.student_id = st.student_id
        WHERE s.mentor_id = ? AND s.status = 'pending'
        ORDER BY s.submitted_date DESC
    ''', (mentor_id,)).fetchall()
    conn.close()
    return submissions

def get_pending_submissions_for_coordinator():
    conn = get_db()
    submissions = conn.execute('''
        SELECT s.*, a.activity_name, a.category, st.name as student_name
        FROM submissions s
        JOIN activities a ON s.activity_id = a.activity_id
        JOIN students st ON s.student_id = st.student_id
        WHERE s.status = 'mentor_approved'
        ORDER BY s.submitted_date DESC
    ''').fetchall()
    conn.close()
    return submissions

def get_pending_submissions_for_college():
    conn = get_db()
    submissions = conn.execute('''
        SELECT s.*, a.activity_name, a.category, st.name as student_name
        FROM submissions s
        JOIN activities a ON s.activity_id = a.activity_id
        JOIN students st ON s.student_id = st.student_id
        WHERE s.status = 'coordinator_approved'
        ORDER BY s.submitted_date DESC
    ''').fetchall()
    conn.close()
    return submissions

def get_all_activities():
    conn = get_db()
    activities = conn.execute(
        'SELECT * FROM activities ORDER BY category'
    ).fetchall()
    conn.close()
    return activities

def get_mentor_for_student(student_id, semester):
    """
    Get the assigned mentor for a student in a specific semester.
    Returns mentor_id or None if no assignment found.
    """
    conn = get_db()
    assignment = conn.execute('''
        SELECT mentor_id FROM mentor_assignments
        WHERE student_id = ? AND semester = ?
        ORDER BY assignment_id DESC
        LIMIT 1
    ''', (student_id, semester)).fetchone()
    conn.close()
    return assignment['mentor_id'] if assignment else None


def get_all_assignments():
    """Get all mentor assignments with student and mentor names."""
    conn = get_db()
    assignments = conn.execute('''
        SELECT ma.*, s.name as student_name,
               m.name as mentor_name,
               s.department, s.year
        FROM mentor_assignments ma
        JOIN students s ON ma.student_id = s.student_id
        JOIN mentors m ON ma.mentor_id = m.mentor_id
        ORDER BY ma.semester DESC, s.name
    ''').fetchall()
    conn.close()
    return assignments


def get_assignments_for_student(student_id):
    """Get all mentor assignments for a specific student."""
    conn = get_db()
    assignments = conn.execute('''
        SELECT ma.*, m.name as mentor_name
        FROM mentor_assignments ma
        JOIN mentors m ON ma.mentor_id = m.mentor_id
        WHERE ma.student_id = ?
        ORDER BY ma.semester
    ''', (student_id,)).fetchall()
    conn.close()
    return assignments
def get_current_calendar():
    """Get the currently active semester calendar."""
    conn = get_db()
    calendar = conn.execute('''
        SELECT * FROM academic_calendar
        WHERE is_current = 1
        ORDER BY calendar_id DESC
        LIMIT 1
    ''').fetchone()
    conn.close()
    return calendar

def get_all_calendars():
    """Get all academic calendar entries."""
    conn = get_db()
    calendars = conn.execute('''
        SELECT * FROM academic_calendar
        ORDER BY calendar_id DESC
    ''').fetchall()
    conn.close()
    return calendars

def get_eligible_students(current_semester):
    """
    Get all students eligible to advance to next semester.
    Eligible = currently in current_semester and not graduated.
    """
    conn = get_db()

    # Max semester depends on student type
    students = conn.execute('''
        SELECT * FROM students
        WHERE semester = ?
        AND is_graduated = 0
        AND (
            (student_type = 'regular' AND semester < 8)
            OR
            (student_type = 'lateral' AND semester < 6)
        )
        ORDER BY department, student_id
    ''', (current_semester,)).fetchall()
    conn.close()
    return students

def advance_students(student_ids, academic_year):
    """
    Advance selected students to next semester.
    Also updates year when crossing semester boundary.
    """
    conn = get_db()

    for student_id in student_ids:
        student = conn.execute(
            'SELECT * FROM students WHERE student_id = ?',
            (student_id,)
        ).fetchone()

        if not student:
            continue

        current_sem = student['semester']
        current_year = student['year']
        new_sem = current_sem + 1

        # Calculate new year
        # Year changes when semester crosses even to odd
        # Sem 2→3, Sem 4→5, Sem 6→7
        new_year = current_year
        if current_sem in [2, 4, 6]:
            new_year = current_year + 1

        # Check if student is graduating
        is_graduated = 0
        if student['student_type'] == 'regular' and new_sem > 8:
            is_graduated = 1
            new_sem = 8  # Keep at 8
        elif student['student_type'] == 'lateral' and new_sem > 6:
            is_graduated = 1
            new_sem = 6  # Keep at 6

        conn.execute('''
            UPDATE students
            SET semester = ?, year = ?,
                is_graduated = ?
            WHERE student_id = ?
        ''', (new_sem, new_year, is_graduated, student_id))

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()