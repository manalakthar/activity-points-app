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
    # Admin table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            admin_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
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
            FOREIGN KEY (student_id) REFERENCES students (student_id),
            FOREIGN KEY (activity_id) REFERENCES activities (activity_id)
        )
    ''')

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
    print("✅ Database initialized successfully!")
    print("✅ All tables created!")
    print("✅ Activities pre-loaded!")

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

if __name__ == '__main__':
    init_db()