from database import get_db, init_db

def add_test_data():
    init_db()
    conn = get_db()
    
    print("Adding test data...")

    # Add a test student
    try:
        conn.execute('''
            INSERT INTO students 
            (student_id, name, email, password, department,
             year, semester, student_type, points_required, total_points)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('4SO21CS001', 'Manal Akthar', 'manal@sjec.ac.in',
              'test123', 'Computer Science', 2, 4, 'regular', 100, 45))
        print("✅ Test student added")
    except Exception as e:
        print(f"Student already exists: {e}")

    # Add a test mentor
    try:
        conn.execute('''
            INSERT INTO mentors
            (mentor_id, name, email, password, department)
            VALUES (?, ?, ?, ?, ?)
        ''', ('M001', 'Prof. John', 'john@sjec.ac.in',
              'mentor123', 'Computer Science'))
        print("✅ Test mentor added")
    except Exception as e:
        print(f"Mentor already exists: {e}")

    # Add a departmental coordinator
    try:
        conn.execute('''
            INSERT INTO coordinators
            (coordinator_id, name, email, password, role, department)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('C001', 'Prof. Sarah', 'sarah@sjec.ac.in',
              'coord123', 'departmental', 'Computer Science'))
        print("✅ Test departmental coordinator added")
    except Exception as e:
        print(f"Coordinator already exists: {e}")

    # Add a college coordinator
    try:
        conn.execute('''
            INSERT INTO coordinators
            (coordinator_id, name, email, password, role, department)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('C002', 'Prof. David', 'david@sjec.ac.in',
              'college123', 'college', None))
        print("✅ Test college coordinator added")
    except Exception as e:
        print(f"College coordinator already exists: {e}")

    # Add a test submission
    try:
        conn.execute('''
            INSERT INTO submissions
            (student_id, activity_id, role, organized_by,
             activity_date, duration_hours, points_claimed,
             extracted_text, face_matched, protsaha_updated,
             status, mentor_id, submitted_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('4SO21CS001', 1, 'participant', 'SJEC NSS',
              '2024-03-15', 6, 10,
              'Certificate of Participation\nManal Akthar\nNSS Activity',
              1, 1, 'pending', 'M001', '2024-03-16 10:00:00'))
        print("✅ Test submission added")
    except Exception as e:
        print(f"Submission already exists: {e}")

    conn.commit()
    conn.close()

    print("\n✅ All test data added successfully!")
    print("\nTest Login Credentials:")
    print("------------------------")
    print("Student:")
    print("  Email: manal@sjec.ac.in")
    print("  Password: test123")
    print("  Role: student")
    print("\nMentor:")
    print("  Email: john@sjec.ac.in")
    print("  Password: mentor123")
    print("  Role: mentor")
    print("\nDepartmental Coordinator:")
    print("  Email: sarah@sjec.ac.in")
    print("  Password: coord123")
    print("  Role: coordinator")
    print("\nCollege Coordinator:")
    print("  Email: david@sjec.ac.in")
    print("  Password: college123")
    print("  Role: coordinator")

if __name__ == '__main__':
    add_test_data()