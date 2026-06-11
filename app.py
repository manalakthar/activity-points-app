from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
from datetime import datetime
import os
from database import (
    init_db, get_db, get_student, get_student_by_email,
    get_submissions_by_student,
    sync_student_total_points,
    get_student_submission,
    get_pending_submissions_for_mentor,
    get_pending_submissions_for_coordinator,
    get_pending_submissions_for_college,
    get_all_activities, get_mentor_for_student,
    get_all_assignments, get_current_calendar,
    get_all_calendars, get_eligible_students,
    advance_students, get_read_notification_keys, mark_notifications_read
)

app = Flask(__name__)
app.secret_key = 'sjec_sap_secret_key'

# Folders
UPLOAD_FOLDER = 'uploads'
KNOWN_FACES_DIR = 'known_faces'
ALLOWED_PHOTO_EXTENSIONS = {'.jpg', '.jpeg', '.png'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(KNOWN_FACES_DIR, exist_ok=True)


def save_student_face_photo(student_id, face_photo):
    """Save a student's reference face photo for profile and verification."""
    if not face_photo or not face_photo.filename:
        return None, 'No photo selected.'

    extension = os.path.splitext(face_photo.filename)[1].lower()
    if extension not in ALLOWED_PHOTO_EXTENSIONS:
        return None, 'Please upload a JPG or PNG image.'

    for ext in ALLOWED_PHOTO_EXTENSIONS:
        old_path = os.path.join(KNOWN_FACES_DIR, f'{student_id}{ext}')
        if os.path.exists(old_path):
            os.remove(old_path)

    path = os.path.join(KNOWN_FACES_DIR, f'{student_id}{extension}')
    face_photo.save(path)
    return path, None


def resolve_student_mentor(student):
    """Return assigned mentor for the student's current semester, if any."""
    mentor_id = get_mentor_for_student(
        student['student_id'], student['semester']
    )
    if not mentor_id:
        return None, None

    conn = get_db()
    mentor = conn.execute(
        'SELECT mentor_id, name FROM mentors WHERE mentor_id = ?',
        (mentor_id,)
    ).fetchone()
    conn.close()

    if not mentor:
        return None, None
    return mentor['mentor_id'], mentor['name']


def process_certificate_upload(certificate, student_id):
    """Save certificate and run OCR / face verification."""
    if not certificate or not certificate.filename:
        return None, None, 0

    extension = os.path.splitext(certificate.filename)[1].lower()
    filename = f"{student_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}{extension}"
    certificate_path = os.path.join(UPLOAD_FOLDER, filename)
    certificate.save(certificate_path)

    extracted_text = None
    face_matched = False

    try:
        from modules.ocr import extract_text
        extracted_text = extract_text(certificate_path)
    except Exception as e:
        print(f"[OCR] Error during text extraction: {e}")

    try:
        from modules.face_auth import verify_student
        face_matched = verify_student(
            certificate_path, student_id, KNOWN_FACES_DIR
        )
    except Exception as e:
        print(f"[FACE] Face recognition error for student={student_id}: {e}")

    return certificate_path, extracted_text, 1 if face_matched else 0


def render_submit_form(student, mentor_id, mentor_name, activities,
                       resubmit_submission=None, error=None):
    return render_template(
        'submit_claim.html',
        activities=activities,
        student=student,
        mentor_assigned=mentor_id is not None,
        mentor_name=mentor_name,
        resubmit_submission=resubmit_submission,
        error=error,
    )

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
# FORGOT PASSWORD
# ============================================================

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        role = request.form.get('role')
        user_id = request.form.get('user_id')
        email = request.form.get('email')
        new_password = request.form.get('new_password')

        conn = get_db()
        
        table = ""
        id_col = ""
        if role == 'student':
            table = "students"
            id_col = "student_id"
        elif role == 'mentor':
            table = "mentors"
            id_col = "mentor_id"
        elif role == 'coordinator':
            table = "coordinators"
            id_col = "coordinator_id"

        # Check if user exists with this ID and Email
        user = conn.execute(
            f'SELECT * FROM {table} WHERE {id_col} = ? AND email = ?',
            (user_id, email)
        ).fetchone()

        if user:
            # Update password
            conn.execute(
                f'UPDATE {table} SET password = ? WHERE {id_col} = ?',
                (new_password, user_id)
            )
            conn.commit()
            conn.close()
            return render_template('forgot_password.html', 
                                   success='Password has been reset successfully!')
        
        conn.close()
        return render_template('forgot_password.html', 
                               error='Invalid ID or Email combination')

    return render_template('forgot_password.html')

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
        photo_error = None

        if face_photo and face_photo.filename:
            face_photo_path, photo_error = save_student_face_photo(
                student_id, face_photo
            )
            if photo_error:
                return render_template('register.html', error=photo_error)

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
            print(f"Registration error: {e}")
            import sqlite3 as _sqlite3
            if isinstance(e, _sqlite3.IntegrityError) and 'UNIQUE' in str(e):
                error_msg = 'Registration failed. A student with this USN or email already exists.'
            else:
                error_msg = f'Registration failed: {e}'
            try:
                conn.close()
            except Exception:
                pass
            return render_template('register.html', error=error_msg)

    return render_template('register.html')

# ============================================================
# STUDENT DASHBOARD
# ============================================================

@app.route('/student/dashboard')
def student_dashboard():
    if session.get('role') != 'student':
        return redirect(url_for('login'))

    sync_student_total_points(session['user_id'])
    student = get_student(session['user_id'])
    submissions = get_submissions_by_student(session['user_id'])
    mentor_id, mentor_name = resolve_student_mentor(student)

    return render_template('student_dashboard.html',
                           student=student,
                           submissions=submissions,
                           mentor_assigned=mentor_id is not None,
                           mentor_name=mentor_name)

# ============================================================
# STUDENT PROFILE
# ============================================================

@app.route('/student/profile', methods=['GET', 'POST'])
def student_profile():
    if session.get('role') != 'student':
        return redirect(url_for('login'))

    student_id = session['user_id']
    success_message = None
    error_message = None

    if request.method == 'POST':
        face_photo = request.files.get('face_photo')
        face_photo_path, photo_error = save_student_face_photo(
            student_id, face_photo
        )

        if photo_error:
            error_message = photo_error
        else:
            conn = get_db()
            conn.execute('''
                UPDATE students SET face_photo_path = ?
                WHERE student_id = ?
            ''', (face_photo_path, student_id))
            conn.commit()
            conn.close()
            success_message = 'Profile photo updated successfully.'

    sync_student_total_points(student_id)
    student = get_student(student_id)
    submissions = get_submissions_by_student(student_id)
    has_photo = (
        student['face_photo_path']
        and os.path.exists(student['face_photo_path'])
    )

    return render_template('student_profile.html',
                           student=student,
                           submissions=submissions,
                           has_photo=has_photo,
                           success_message=success_message,
                           error_message=error_message)


@app.route('/student/profile/photo')
def student_profile_photo():
    if session.get('role') != 'student':
        return redirect(url_for('login'))

    student = get_student(session['user_id'])
    if not student['face_photo_path']:
        return '', 404

    photo_path = student['face_photo_path']
    if not os.path.exists(photo_path):
        return '', 404

    directory = os.path.dirname(photo_path) or KNOWN_FACES_DIR
    filename = os.path.basename(photo_path)
    return send_from_directory(directory, filename)

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

    student = get_student(session['user_id'])
    mentor_id, mentor_name = resolve_student_mentor(student)
    activities = get_all_activities()

    if request.method == 'POST':
        if not mentor_id:
            return render_submit_form(
                student, mentor_id, mentor_name, activities,
                error=(
                    'You cannot submit this activity because no faculty '
                    'mentor has been assigned to you for this semester. '
                    'Please contact your department coordinator or admin.'
                ),
            )

        activity_id = request.form.get('activity_id')
        role = request.form.get('role')
        organized_by = request.form.get('organized_by')
        activity_date = request.form.get('activity_date')
        duration_hours = request.form.get('duration_hours')
        points_claimed = request.form.get('points_claimed')
        protsaha_updated = 1 if request.form.get('protsaha_updated') else 0

        certificate = request.files.get('certificate')
        certificate_path, extracted_text, face_matched = (
            process_certificate_upload(certificate, session['user_id'])
        )

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
              protsaha_updated, mentor_id,
              datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

        conn.commit()
        conn.close()

        return redirect(url_for('student_dashboard'))

    return render_submit_form(student, mentor_id, mentor_name, activities)


@app.route('/student/resubmit/<int:submission_id>', methods=['GET', 'POST'])
def resubmit_claim(submission_id):
    if session.get('role') != 'student':
        return redirect(url_for('login'))

    student = get_student(session['user_id'])
    mentor_id, mentor_name = resolve_student_mentor(student)
    activities = get_all_activities()
    existing = get_student_submission(submission_id, session['user_id'])

    if not existing or existing['status'] != 'rejected':
        return redirect(url_for('student_dashboard'))

    if request.method == 'POST':
        if not mentor_id:
            return render_submit_form(
                student, mentor_id, mentor_name, activities,
                resubmit_submission=existing,
                error=(
                    'You cannot resubmit this activity because no faculty '
                    'mentor has been assigned to you for this semester. '
                    'Please contact your department coordinator or admin.'
                ),
            )

        certificate = request.files.get('certificate')
        certificate_path = existing['certificate_path']
        extracted_text = existing['extracted_text']
        face_matched = existing['face_matched']

        if certificate and certificate.filename:
            certificate_path, extracted_text, face_matched = (
                process_certificate_upload(certificate, session['user_id'])
            )

        conn = get_db()
        conn.execute('''
            UPDATE submissions
            SET activity_id = ?, role = ?, organized_by = ?, activity_date = ?,
                duration_hours = ?, points_claimed = ?,
                certificate_path = ?, extracted_text = ?, face_matched = ?,
                protsaha_updated = ?, status = 'pending', mentor_id = ?,
                submitted_date = ?, reviewed_date = NULL,
                rejection_note = NULL, points_awarded = 0
            WHERE submission_id = ? AND student_id = ? AND status = 'rejected'
        ''', (
            request.form.get('activity_id'),
            request.form.get('role'),
            request.form.get('organized_by'),
            request.form.get('activity_date'),
            request.form.get('duration_hours'),
            request.form.get('points_claimed'),
            certificate_path,
            extracted_text,
            face_matched,
            1 if request.form.get('protsaha_updated') else 0,
            mentor_id,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            submission_id,
            session['user_id'],
        ))
        conn.execute('''
            DELETE FROM notification_reads
            WHERE notification_key = ?
        ''', (f'm-pending-{submission_id}',))
        conn.commit()
        conn.close()

        return redirect(url_for('student_dashboard'))

    return render_submit_form(
        student, mentor_id, mentor_name, activities,
        resubmit_submission=existing,
    )

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
        rejection_note = request.form.get('rejection_note', '')
        status = 'mentor_approved' if action == 'approve' else 'rejected'

        conn.execute('''
            UPDATE submissions
            SET status = ?, reviewed_date = ?,
            rejection_note = ?
            WHERE submission_id = ?
        ''', (status, datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
              rejection_note if action == 'reject' else None,
              submission_id))
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
        rejection_note = request.form.get('rejection_note', '')

        if action == 'approve':
            conn.execute('''
                UPDATE submissions
                SET status = 'approved', points_awarded = ?,
                reviewed_date = ?, rejection_note = NULL
                WHERE submission_id = ?
            ''', (points_awarded,
                  datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                  submission_id))

            submission = conn.execute(
                'SELECT student_id FROM submissions '
                'WHERE submission_id = ?',
                (submission_id,)
            ).fetchone()

            conn.commit()
            conn.close()
            sync_student_total_points(submission['student_id'])

        else:
            conn.execute('''
                UPDATE submissions
                SET status = 'rejected', reviewed_date = ?,
                rejection_note = ?
                WHERE submission_id = ?
            ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                  rejection_note, submission_id))
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
# COLLEGE DASHBOARD
# ============================================================

@app.route('/college/dashboard')
def college_dashboard():
    if session.get('role') != 'college':
        return redirect(url_for('login'))

    submissions = get_pending_submissions_for_college()

    conn = get_db()
    watchlist = conn.execute(
        'SELECT * FROM students WHERE watch_list = 1'
    ).fetchall()
    conn.close()

    return render_template('college_dashboard.html',
                           submissions=submissions,
                           watchlist=watchlist,
                           name=session['name'])

# ============================================================
# COLLEGE FINAL APPROVAL
# ============================================================

@app.route('/college/review/<int:submission_id>', methods=['GET', 'POST'])
def college_review(submission_id):
    if session.get('role') != 'college':
        return redirect(url_for('login'))

    conn = get_db()

    if request.method == 'POST':
        action = request.form.get('action')
        points_awarded = int(request.form.get('points_awarded', 0))

        if action == 'approve':
            # Update submission
            conn.execute('''
                UPDATE submissions
                SET status = 'approved', points_awarded = ?,
                reviewed_date = ?
                WHERE submission_id = ?
            ''', (points_awarded,
                  datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                  submission_id))

            # Get student id from submission
            submission = conn.execute(
                'SELECT student_id FROM submissions WHERE submission_id = ?',
                (submission_id,)
            ).fetchone()

            # Add points to student
            conn.commit()
            conn.close()
            sync_student_total_points(submission['student_id'])

        else:
            conn.execute('''
                UPDATE submissions
                SET status = 'rejected', reviewed_date = ?
                WHERE submission_id = ?
            ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), submission_id))
            conn.commit()
            conn.close()

        return redirect(url_for('college_dashboard'))

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

    return render_template('college_review.html', submission=submission)

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
# ============================================================
# ADMIN LOGIN
# ============================================================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        print(f"[ADMIN LOGIN] Received email=[{email}] password=[{password}]")

        conn = get_db()
        admin = conn.execute(
            'SELECT * FROM admins WHERE email = ? AND password = ?',
            (email, password)
        ).fetchone()

        # Debug: also check if the email exists at all
        admin_by_email = conn.execute(
            'SELECT email, password FROM admins WHERE email = ?',
            (email,)
        ).fetchone()
        if admin_by_email:
            print(f"[ADMIN LOGIN] DB has email=[{admin_by_email['email']}] password=[{admin_by_email['password']}]")
        else:
            print(f"[ADMIN LOGIN] No admin found with email=[{email}]")
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
# ADMIN — BULK MENTOR ASSIGNMENT
# ============================================================

@app.route('/admin/bulk_assign', methods=['GET', 'POST'])
def bulk_assign():
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))

    conn = get_db()
    mentors = conn.execute(
        'SELECT * FROM mentors ORDER BY name'
    ).fetchall()

    departments = conn.execute('''
        SELECT DISTINCT department, semester
        FROM students
        ORDER BY department, semester
    ''').fetchall()

    selected_dept = request.args.get('department', '')
    selected_sem = request.args.get('semester', '')
    group_size = int(request.args.get('group_size', 6))

    students = []
    if selected_dept and selected_sem:
        students = conn.execute('''
            SELECT s.*,
                   ma.mentor_id as assigned_mentor_id,
                   m.name as assigned_mentor_name
            FROM students s
            LEFT JOIN mentor_assignments ma
                ON s.student_id = ma.student_id
                AND ma.semester = ?
            LEFT JOIN mentors m
                ON ma.mentor_id = m.mentor_id
            WHERE s.department = ? AND s.semester = ?
            ORDER BY s.student_id
        ''', (selected_sem, selected_dept,
              selected_sem)).fetchall()

    conn.close()

    # Auto divide into groups based on group_size
    groups = []
    for i in range(0, len(students), group_size):
        groups.append(list(students[i:i + group_size]))

    return render_template('admin_bulk_assign.html',
                           mentors=mentors,
                           departments=departments,
                           students=students,
                           groups=groups,
                           selected_dept=selected_dept,
                           selected_sem=selected_sem,
                           group_size=group_size)


@app.route('/admin/bulk_assign/save', methods=['POST'])
def bulk_assign_save():
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))

    academic_year = request.form.get('academic_year')
    semester = request.form.get('semester')
    department = request.form.get('department')

    # Get all group mentor assignments from form
    # Form sends: group_0_mentor, group_1_mentor, etc.
    # And group_0_students = comma separated student IDs

    conn = get_db()
    assigned_count = 0

    group_index = 0
    while True:
        mentor_id = request.form.get(f'group_{group_index}_mentor')
        student_ids = request.form.get(f'group_{group_index}_students')

        if mentor_id is None:
            break

        if student_ids and mentor_id:
            for student_id in student_ids.split(','):
                student_id = student_id.strip()
                if not student_id:
                    continue

                # Check if assignment already exists
                existing = conn.execute('''
                    SELECT assignment_id FROM mentor_assignments
                    WHERE student_id = ? AND semester = ?
                ''', (student_id, semester)).fetchone()

                if existing:
                    # Update existing
                    conn.execute('''
                        UPDATE mentor_assignments
                        SET mentor_id = ?, academic_year = ?
                        WHERE student_id = ? AND semester = ?
                    ''', (mentor_id, academic_year,
                          student_id, semester))
                else:
                    # Create new
                    conn.execute('''
                        INSERT INTO mentor_assignments
                        (student_id, mentor_id, semester, academic_year)
                        VALUES (?, ?, ?, ?)
                    ''', (student_id, mentor_id,
                          semester, academic_year))

                assigned_count += 1

        group_index += 1

    conn.commit()
    conn.close()

    return redirect(url_for('bulk_assign',
                            department=department,
                            semester=semester,
                            success=assigned_count))
# ============================================================
# ADMIN — ACADEMIC CALENDAR
# ============================================================

@app.route('/admin/calendar', methods=['GET', 'POST'])
def admin_calendar():
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))

    from database import get_all_calendars, get_current_calendar

    if request.method == 'POST':
        semester = request.form.get('semester')
        academic_year = request.form.get('academic_year')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        is_current = 1 if request.form.get('is_current') else 0

        conn = get_db()

        # If setting as current, unset all others first
        if is_current:
            conn.execute(
                'UPDATE academic_calendar SET is_current = 0'
            )

        conn.execute('''
            INSERT INTO academic_calendar
            (semester, academic_year, start_date,
             end_date, is_current, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (semester, academic_year, start_date,
              end_date, is_current,
              datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

        conn.commit()
        conn.close()
        return redirect(url_for('admin_calendar'))

    calendars = get_all_calendars()
    current = get_current_calendar()
    return render_template('admin_calendar.html',
                           calendars=calendars,
                           current=current)


@app.route('/admin/calendar/set_current/<int:calendar_id>')
def set_current_calendar(calendar_id):
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))

    conn = get_db()
    conn.execute('UPDATE academic_calendar SET is_current = 0')
    conn.execute(
        'UPDATE academic_calendar SET is_current = 1 WHERE calendar_id = ?',
        (calendar_id,)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('admin_calendar'))


@app.route('/admin/calendar/delete/<int:calendar_id>')
def delete_calendar(calendar_id):
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))

    conn = get_db()
    conn.execute(
        'DELETE FROM academic_calendar WHERE calendar_id = ?',
        (calendar_id,)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('admin_calendar'))


# ============================================================
# ADMIN — ADVANCE SEMESTER
# ============================================================

@app.route('/admin/advance_semester', methods=['GET', 'POST'])
def advance_semester():
    if session.get('role') != 'admin':
        return redirect(url_for('admin_login'))

    from database import (get_current_calendar,
                          get_eligible_students, advance_students)

    current_calendar = get_current_calendar()
    eligible_students = []
    success_message = None

    if current_calendar:
        eligible_students = get_eligible_students(
            current_calendar['semester']
        )

    if request.method == 'POST':
        # Get selected student IDs from form
        selected_ids = request.form.getlist('student_ids')
        academic_year = request.form.get('academic_year')

        if selected_ids:
            advance_students(selected_ids, academic_year)
            success_message = (
                f"Successfully advanced {len(selected_ids)} "
                f"students to next semester!"
            )
            # Refresh eligible students list
            if current_calendar:
                eligible_students = get_eligible_students(
                    current_calendar['semester']
                )

    return render_template('admin_advance_semester.html',
                           current_calendar=current_calendar,
                           eligible_students=eligible_students,
                           success_message=success_message)

# ============================================================
# RUN APP
# ============================================================

@app.route('/notifications')
def get_notifications():
    if not session.get('user_id'):
        return jsonify([])

    user_id = session['user_id']
    role = session.get('role')
    read_keys = get_read_notification_keys(user_id, role)

    conn = get_db()
    notifications = []

    if role == 'student':
        reviewed = conn.execute('''
            SELECT s.submission_id, a.activity_name, s.status, s.points_awarded
            FROM submissions s
            JOIN activities a ON s.activity_id = a.activity_id
            WHERE s.student_id = ?
            AND s.status IN ('approved', 'rejected', 'mentor_approved')
        ''', (user_id,)).fetchall()

        for r in reviewed:
            notif_id = f"s-{r['submission_id']}-{r['status']}"
            if notif_id in read_keys:
                continue
            if r['status'] == 'approved':
                notifications.append({
                    'id': notif_id,
                    'message': f"✅ Your claim for '{r['activity_name']}' was approved! {r['points_awarded']} pts awarded.",
                    'type': 'success'
                })
            elif r['status'] == 'rejected':
                notifications.append({
                    'id': notif_id,
                    'message': f"❌ Your claim for '{r['activity_name']}' was rejected.",
                    'type': 'error'
                })
            elif r['status'] == 'mentor_approved':
                notifications.append({
                    'id': notif_id,
                    'message': f"🔄 Your claim for '{r['activity_name']}' is under coordinator review.",
                    'type': 'info'
                })

    elif role == 'mentor':
        pending = conn.execute('''
            SELECT submission_id FROM submissions
            WHERE mentor_id = ? AND status = 'pending'
            ORDER BY submission_id
        ''', (user_id,)).fetchall()

        unread_ids = [
            p['submission_id'] for p in pending
            if f"m-pending-{p['submission_id']}" not in read_keys
        ]
        if unread_ids:
            notif_id = 'm-pending-' + '-'.join(str(i) for i in unread_ids)
            notifications.append({
                'id': notif_id,
                'message': f"📋 You have {len(unread_ids)} pending submission(s) to review.",
                'type': 'warning'
            })

    elif role in ('departmental', 'college'):
        pending = conn.execute('''
            SELECT submission_id FROM submissions
            WHERE status = 'mentor_approved'
            ORDER BY submission_id
        ''').fetchall()

        unread_ids = [
            p['submission_id'] for p in pending
            if f"c-pending-{p['submission_id']}" not in read_keys
        ]
        if unread_ids:
            notif_id = 'c-pending-' + '-'.join(str(i) for i in unread_ids)
            notifications.append({
                'id': notif_id,
                'message': f"📋 {len(unread_ids)} submission(s) are waiting for your review.",
                'type': 'warning'
            })

    conn.close()
    return jsonify(notifications)


@app.route('/notifications/read', methods=['POST'])
def read_notifications():
    if not session.get('user_id'):
        return jsonify({'ok': False}), 401

    data = request.get_json(silent=True) or {}
    keys = data.get('keys', [])
    expanded_keys = []

    for key in keys:
        if key.startswith('m-pending-'):
            suffix = key[len('m-pending-'):]
            if suffix:
                for submission_id in suffix.split('-'):
                    expanded_keys.append(f'm-pending-{submission_id}')
        elif key.startswith('c-pending-'):
            suffix = key[len('c-pending-'):]
            if suffix:
                for submission_id in suffix.split('-'):
                    expanded_keys.append(f'c-pending-{submission_id}')
        else:
            expanded_keys.append(key)

    mark_notifications_read(session['user_id'], session.get('role'), expanded_keys)
    return jsonify({'ok': True})

if __name__ == '__main__':
    app.run(debug=True)