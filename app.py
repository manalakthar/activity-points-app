from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
from datetime import datetime
import os
from database import (
    init_db, get_db, get_student, get_student_by_email,
    update_student_points, get_submissions_by_student,
    get_pending_submissions_for_mentor,
    get_pending_submissions_for_coordinator,
    get_all_activities, get_mentor_for_student,
    get_all_assignments
)

app = Flask(__name__)
app.secret_key = 'sjec_sap_secret_key'

# Folders
UPLOAD_FOLDER = 'uploads'
KNOWN_FACES_DIR = 'known_faces'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(KNOWN_FACES_DIR, exist_ok=True)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# Initialize database when app starts
init_db()

# ============================================================
# HOME
# ============================================================

@app.route('/')
def home():
    return redirect(url_for('login'))

# ============================================================
# LOGIN
# ============================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')  # student/mentor/coordinator

        conn = get_db()

        if role == 'student':
            user = conn.execute(
                'SELECT * FROM students WHERE email = ? AND password = ?',
                (email, password)
            ).fetchone()
            if user:
                session['user_id'] = user['student_id']
                session['role'] = 'student'
                session['name'] = user['name']
                conn.close()
                return redirect(url_for('student_dashboard'))

        elif role == 'mentor':
            user = conn.execute(
                'SELECT * FROM mentors WHERE email = ? AND password = ?',
                (email, password)
            ).fetchone()
            if user:
                session['user_id'] = user['mentor_id']
                session['role'] = 'mentor'
                session['name'] = user['name']
                conn.close()
                return redirect(url_for('mentor_dashboard'))

        elif role == 'coordinator':
            user = conn.execute(
                'SELECT * FROM coordinators WHERE email = ? AND password = ?',
                (email, password)
            ).fetchone()
            if user:
                session['user_id'] = user['coordinator_id']
                session['role'] = user['role']
                session['name'] = user['name']
                conn.close()
                if user['role'] == 'departmental':
                    return redirect(url_for('coordinator_dashboard'))
                else:
                    return redirect(url_for('college_dashboard'))

        conn.close()
        return render_template('login.html', error='Invalid email or password')

    return render_template('login.html')

# ============================================================
# LOGOUT
# ============================================================

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ============================================================
# STUDENT REGISTRATION
# ============================================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        department = request.form.get('department')
        year = request.form.get('year')
        semester = request.form.get('semester')
        student_type = request.form.get('student_type')
        points_required = 75 if student_type == 'lateral' else 100

        # Handle face photo upload
        face_photo = request.files.get('face_photo')
        face_photo_path = None

        if face_photo:
            extension = os.path.splitext(face_photo.filename)[1].lower()
            face_photo_path = os.path.join(
                KNOWN_FACES_DIR, f'{student_id}{extension}'
            )
            face_photo.save(face_photo_path)

        try:
            conn = get_db()
            conn.execute('''
                INSERT INTO students 
                (student_id, name, email, password, department, 
                 year, semester, student_type, points_required, face_photo_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (student_id, name, email, password, department,
                  year, semester, student_type, points_required, face_photo_path))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))

        except Exception as e:
            return render_template('register.html', error='Registration failed. USN or email already exists.')

    return render_template('register.html')

# ============================================================
# STUDENT DASHBOARD
# ============================================================

@app.route('/student/dashboard')
def student_dashboard():
    if session.get('role') != 'student':
        return redirect(url_for('login'))

    student = get_student(session['user_id'])
    submissions = get_submissions_by_student(session['user_id'])

    return render_template('student_dashboard.html',
                           student=student,
                           submissions=submissions)

# ============================================================
# STUDENT PROFILE
# ============================================================

@app.route('/student/profile')
def student_profile():
    if session.get('role') != 'student':
        return redirect(url_for('login'))

    student = get_student(session['user_id'])
    submissions = get_submissions_by_student(session['user_id'])

    return render_template('student_profile.html',
                           student=student,
                           submissions=submissions)

# ============================================================
# ACTIVITIES PAGE
# ============================================================

@app.route('/activities')
def activities():
    all_activities = get_all_activities()
    return render_template('activities.html', activities=all_activities)

# ============================================================
# SUBMIT CLAIM
# ============================================================

@app.route('/student/submit', methods=['GET', 'POST'])
def submit_claim():
    if session.get('role') != 'student':
        return redirect(url_for('login'))

    if request.method == 'POST':
        activity_id = request.form.get('activity_id')
        role = request.form.get('role')
        organized_by = request.form.get('organized_by')
        activity_date = request.form.get('activity_date')
        duration_hours = request.form.get('duration_hours')
        points_claimed = request.form.get('points_claimed')
        protsaha_updated = 1 if request.form.get('protsaha_updated') else 0

        # Handle certificate upload
        certificate = request.files.get('certificate')
        certificate_path = None
        extracted_text = None
        face_matched = False

        if certificate:
            extension = os.path.splitext(certificate.filename)[1].lower()
            filename = f"{session['user_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}{extension}"
            certificate_path = os.path.join(UPLOAD_FOLDER, filename)
            certificate.save(certificate_path)

            # Run OCR on certificate
            try:
                from modules.ocr import extract_text
                extracted_text = extract_text(certificate_path)
            except Exception as e:
                print(f"OCR error: {e}")

            # Run face recognition
            # Run face recognition
            try:
               from modules.face_auth import verify_student
               face_matched = verify_student(
               certificate_path,
               session['user_id'],
                KNOWN_FACES_DIR
    )
            except Exception as e:
             print(f"Face recognition error: {e}")

        # Get assigned mentor for this student's current semester
        student = get_student(session['user_id'])
        mentor_id = get_mentor_for_student(
            session['user_id'],
            student['semester']
        )

        # If no assignment found, fall back to department mentor
        if not mentor_id:
            conn_temp = get_db()
            mentor = conn_temp.execute(
                'SELECT mentor_id FROM mentors WHERE department = ?',
                (student['department'],)
            ).fetchone()
            conn_temp.close()
            mentor_id = mentor['mentor_id'] if mentor else None
        conn = get_db()
        conn.execute('''
            INSERT INTO submissions
            (student_id, activity_id, role, organized_by, activity_date,
             duration_hours, points_claimed, certificate_path, extracted_text,
             face_matched, protsaha_updated, status, mentor_id, submitted_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
        ''', (session['user_id'], activity_id, role, organized_by,
              activity_date, duration_hours, points_claimed,
              certificate_path, extracted_text, face_matched,
              protsaha_updated, mentor_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

        conn.commit()
        conn.close()

        return redirect(url_for('student_dashboard'))

    activities = get_all_activities()
    return render_template('submit_claim.html', activities=activities)

# ============================================================
# MENTOR DASHBOARD
# ============================================================

@app.route('/mentor/dashboard')
def mentor_dashboard():
    if session.get('role') != 'mentor':
        return redirect(url_for('login'))

    submissions = get_pending_submissions_for_mentor(session['user_id'])
    return render_template('mentor_dashboard.html',
                           submissions=submissions,
                           name=session['name'])

# ============================================================
# MENTOR REVIEW
# ============================================================

@app.route('/mentor/review/<int:submission_id>', methods=['GET', 'POST'])
def mentor_review(submission_id):
    if session.get('role') != 'mentor':
        return redirect(url_for('login'))

    conn = get_db()

    if request.method == 'POST':
        action = request.form.get('action')
        status = 'mentor_approved' if action == 'approve' else 'rejected'

        conn.execute('''
            UPDATE submissions
            SET status = ?, reviewed_date = ?
            WHERE submission_id = ?
        ''', (status, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), submission_id))
        conn.commit()
        conn.close()
        return redirect(url_for('mentor_dashboard'))

    submission = conn.execute('''
        SELECT s.*, a.activity_name, a.category, st.name as student_name
        FROM submissions s
        JOIN activities a ON s.activity_id = a.activity_id
        JOIN students st ON s.student_id = st.student_id
        WHERE s.submission_id = ?
    ''', (submission_id,)).fetchone()
    conn.close()

    return render_template('mentor_review.html', submission=submission)

# ============================================================
# COORDINATOR DASHBOARD
# ============================================================

@app.route('/coordinator/dashboard')
def coordinator_dashboard():
    if session.get('role') != 'departmental':
        return redirect(url_for('login'))

    submissions = get_pending_submissions_for_coordinator()
    return render_template('coordinator_dashboard.html',
                           submissions=submissions,
                           name=session['name'])

# ============================================================
# COORDINATOR REVIEW
# ============================================================

@app.route('/coordinator/review/<int:submission_id>', methods=['GET', 'POST'])
def coordinator_review(submission_id):
    if session.get('role') != 'departmental':
        return redirect(url_for('login'))

    conn = get_db()

    if request.method == 'POST':
        action = request.form.get('action')
        points_awarded = int(request.form.get('points_awarded', 0))

        if action == 'approve':
            # Update submission as fully approved
            conn.execute('''
                UPDATE submissions
                SET status = 'approved', points_awarded = ?,
                reviewed_date = ?
                WHERE submission_id = ?
            ''', (points_awarded,
                  datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                  submission_id))

            # Get student id
            submission = conn.execute(
                'SELECT student_id FROM submissions WHERE submission_id = ?',
                (submission_id,)
            ).fetchone()

            conn.commit()
            conn.close()

            # Add points to student profile
            update_student_points(submission['student_id'], points_awarded)

        else:
            conn.execute('''
                UPDATE submissions
                SET status = 'rejected', reviewed_date = ?
                WHERE submission_id = ?
            ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                  submission_id))
            conn.commit()
            conn.close()

        return redirect(url_for('coordinator_dashboard'))

    submission = conn.execute('''
        SELECT s.*, a.activity_name, a.category,
               a.max_points_participant, a.max_points_organizer,
               st.name as student_name
        FROM submissions s
        JOIN activities a ON s.activity_id = a.activity_id
        JOIN students st ON s.student_id = st.student_id
        WHERE s.submission_id = ?
    ''', (submission_id,)).fetchone()
    conn.close()

    return render_template('coordinator_review.html', submission=submission)

# ============================================================
# WATCHLIST
# ============================================================
@app.route('/coordinator/watchlist')
def watchlist():
    if session.get('role') != 'departmental':
        return redirect(url_for('login'))

    conn = get_db()
    students = conn.execute(
        'SELECT * FROM students WHERE watch_list = 1'
    ).fetchall()
    conn.close()

    return render_template('watchlist.html', students=students)
# ============================================================
# ADMIN LOGIN
# ============================================================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        conn = get_db()
        admin = conn.execute(
            'SELECT * FROM admins WHERE email = ? AND password = ?',
            (email, password)
        ).fetchone()
        conn.close()

        if admin:
            session['user_id'] = admin['admin_id']
            session['role'] = 'admin'
            session['name'] = admin['name']
            return redirect(url_for('admin_dashboard'))

        return render_template('admin_login.html',
                               error='Invalid email or password')

    return render_template('admin_login.html')

# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))

    conn = get_db()
    students = conn.execute(
        'SELECT * FROM students ORDER BY name'
    ).fetchall()
    mentors = conn.execute(
        'SELECT * FROM mentors ORDER BY name'
    ).fetchall()
    coordinators = conn.execute(
        'SELECT * FROM coordinators ORDER BY name'
    ).fetchall()
    conn.close()

    return render_template('admin_dashboard.html',
                           students=students,
                           mentors=mentors,
                           coordinators=coordinators,
                           name=session['name'])

# ============================================================
# ADMIN ADD MENTOR
# ============================================================

@app.route('/admin/add_mentor', methods=['GET', 'POST'])
def admin_add_mentor():
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        mentor_id = request.form.get('mentor_id')
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        department = request.form.get('department')

        try:
            conn = get_db()
            conn.execute('''
                INSERT INTO mentors
                (mentor_id, name, email, password, department)
                VALUES (?, ?, ?, ?, ?)
            ''', (mentor_id, name, email, password, department))
            conn.commit()
            conn.close()
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            return render_template('admin_add_mentor.html',
                                   error='Mentor ID or email already exists')

    return render_template('admin_add_mentor.html')

# ============================================================
# ADMIN ADD COORDINATOR
# ============================================================

@app.route('/admin/add_coordinator', methods=['GET', 'POST'])
def admin_add_coordinator():
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        coordinator_id = request.form.get('coordinator_id')
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        department = request.form.get('department')

        try:
            conn = get_db()
            conn.execute('''
                INSERT INTO coordinators
                (coordinator_id, name, email, password, role, department)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (coordinator_id, name, email, password, role, department))
            conn.commit()
            conn.close()
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            return render_template('admin_add_coordinator.html',
                                   error='Coordinator ID or email already exists')

    return render_template('admin_add_coordinator.html')

# ============================================================
# ADMIN DELETE USER
# ============================================================

@app.route('/admin/delete/<user_type>/<user_id>')
def admin_delete(user_type, user_id):
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))

    conn = get_db()
    if user_type == 'mentor':
        conn.execute('DELETE FROM mentors WHERE mentor_id = ?', (user_id,))
    elif user_type == 'coordinator':
        conn.execute(
            'DELETE FROM coordinators WHERE coordinator_id = ?', (user_id,)
        )
    elif user_type == 'student':
        conn.execute('DELETE FROM students WHERE student_id = ?', (user_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('admin_dashboard'))

# ============================================================
# ADMIN — MENTOR ASSIGNMENTS
# ============================================================

@app.route('/admin/assignments')
def admin_assignments():
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))

    assignments = get_all_assignments()

    conn = get_db()
    students = conn.execute(
        'SELECT * FROM students ORDER BY name'
    ).fetchall()
    mentors = conn.execute(
        'SELECT * FROM mentors ORDER BY name'
    ).fetchall()
    conn.close()

    return render_template('admin_assignments.html',
                           assignments=assignments,
                           students=students,
                           mentors=mentors)


@app.route('/admin/assign_mentor', methods=['POST'])
def assign_mentor():
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))

    student_id = request.form.get('student_id')
    mentor_id = request.form.get('mentor_id')
    semester = request.form.get('semester')
    academic_year = request.form.get('academic_year')

    try:
        conn = get_db()
        # Check if assignment already exists for this
        # student + semester
        existing = conn.execute('''
            SELECT assignment_id FROM mentor_assignments
            WHERE student_id = ? AND semester = ?
        ''', (student_id, semester)).fetchone()

        if existing:
            # Update existing assignment
            conn.execute('''
                UPDATE mentor_assignments
                SET mentor_id = ?, academic_year = ?
                WHERE student_id = ? AND semester = ?
            ''', (mentor_id, academic_year, student_id, semester))
        else:
            # Create new assignment
            conn.execute('''
                INSERT INTO mentor_assignments
                (student_id, mentor_id, semester, academic_year)
                VALUES (?, ?, ?, ?)
            ''', (student_id, mentor_id, semester, academic_year))

        conn.commit()
        conn.close()

    except Exception as e:
        print(f"Assignment error: {e}")

    return redirect(url_for('admin_assignments'))


@app.route('/admin/delete_assignment/<int:assignment_id>')
def delete_assignment(assignment_id):
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))

    conn = get_db()
    conn.execute(
        'DELETE FROM mentor_assignments WHERE assignment_id = ?',
        (assignment_id,)
    )
    conn.commit()
    conn.close()

    return redirect(url_for('admin_assignments'))

# ============================================================
# RUN APP
# ============================================================

if __name__ == '__main__':
    app.run(debug=True)