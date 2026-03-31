import sqlite3

def get_db():
    """Connect to the database."""
    conn = sqlite3.connect('database.db')
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

    conn.commit()
    conn.close()
    print("Database initialized successfully!")

if __name__ == '__main__':
    init_db()