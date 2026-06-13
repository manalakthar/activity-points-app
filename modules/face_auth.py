import face_recognition
import os
import numpy as np
import sys
import tempfile
import urllib.request

# Add parent directory to path so we can import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

SUPPORTED_FORMATS = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')

def load_image_for_face(image_path):
    """
    Load any supported image type for face recognition.
    """
    extension = os.path.splitext(image_path)[1].lower()

    if extension == '.pdf':
        try:
            from pdf2image import convert_from_path
            pages = convert_from_path(image_path)
            img = np.array(pages[0])
            print(f"[FACE] Loaded PDF: {image_path}")
            return img
        except Exception as e:
            print(f"[FACE] PDF load error: {e}")
            return None

    elif extension in SUPPORTED_FORMATS:
        try:
            img = face_recognition.load_image_file(image_path)
            print(f"[FACE] Loaded image: {image_path}")
            return img
        except Exception as e:
            print(f"[FACE] Error loading image {image_path}: {e}")
            return None

    else:
        print(f"[FACE] Unsupported file type: {extension}")
        return None


def load_known_faces(known_faces_dir):
    """
    Load all reference photos from known_faces/ folder.
    Each photo is named after the student's USN/ID.
    Example: 4SO21CS001.jpeg
    Returns encodings and matching names/IDs.
    """
    known_encodings = []
    known_names = []

    print("\n[FACE] Loading known faces...")

    if not os.path.exists(known_faces_dir):
        print(f"[FACE] Directory not found: {known_faces_dir}")
        return known_encodings, known_names

    all_formats = SUPPORTED_FORMATS + ('.pdf',)

    for filename in os.listdir(known_faces_dir):
        if filename.lower().endswith(all_formats):
            name = os.path.splitext(filename)[0]
            image_path = os.path.join(known_faces_dir, filename)
            image = load_image_for_face(image_path)

            if image is None:
                continue

            try:
                encodings = face_recognition.face_encodings(image)
            except Exception as e:
                print(f"[FACE] Error getting encodings for {filename}: {e}")
                continue

            if encodings:
                known_encodings.append(encodings[0])
                known_names.append(name)
                print(f"[FACE] Loaded: {name}")
            else:
                print(f"[FACE] Warning: No face found in {filename}")

    print(f"[FACE] Total known faces: {len(known_names)}")
    return known_encodings, known_names


def recognize_faces(image_path, known_encodings, known_names):
    """
    Find and identify all faces in an image.
    Returns list of matched names/student IDs.
    Used in app.py to verify student identity
    when they upload a certificate.
    """
    print(f"\n[FACE] Scanning: {image_path}")

    image = load_image_for_face(image_path)
    if image is None:
        return []

    # Find all faces in the image
    try:
        face_locations = face_recognition.face_locations(image)
    except Exception as e:
        print(f"[FACE] Error finding face locations: {e}")
        return []

    if not face_locations:
        print("[FACE] No faces found")
        return []

    print(f"[FACE] Found {len(face_locations)} face(s)")

    # Get encodings for found faces
    try:
        face_encodings = face_recognition.face_encodings(image, face_locations)
    except Exception as e:
        print(f"[FACE] Error getting face encodings: {e}")
        return []

    results = []

    for face_encoding, location in zip(face_encodings, face_locations):
        matches = face_recognition.compare_faces(
            known_encodings, face_encoding
        )

        name = "Unknown"

        if True in matches:
            face_distances = face_recognition.face_distance(
                known_encodings, face_encoding
            )
            best_match_index = face_distances.argmin()

            if matches[best_match_index]:
                name = known_names[best_match_index]

        results.append(name)
        print(f"[FACE] Identified: {name}")

    return results


def verify_student(image_path, student_id, known_faces_dir):
    """
    Verify if a specific student is present in an uploaded image.
    Returns True if student is found, False otherwise.

    This is the main function called from app.py:
    face_matched = verify_student(certificate_path, student_id, KNOWN_FACES_DIR)
    """
    # 1. Find the known face photo for this student
    known_image_path = None

    # Check if student's face_photo_path is a URL in the database
    try:
        import database
        student = database.get_student(student_id)
        if student and student.get('face_photo_path'):
            photo_path = student['face_photo_path']
            if photo_path.startswith('http'):
                ext = os.path.splitext(photo_path.split('?')[0])[1].lower() or '.jpeg'
                local_download_path = os.path.join(known_faces_dir, f"{student_id}_db{ext}")
                print(f"[FACE] Downloading DB face photo: {photo_path} to {local_download_path}")
                urllib.request.urlretrieve(photo_path, local_download_path)
                known_image_path = local_download_path
            elif os.path.exists(photo_path):
                known_image_path = photo_path
    except Exception as e:
        print(f"[FACE] Error fetching/downloading face photo from DB: {e}")

    # Fallback to scanning local directory
    if not known_image_path:
        all_formats = SUPPORTED_FORMATS + ('.pdf',)
        if os.path.exists(known_faces_dir):
            for filename in os.listdir(known_faces_dir):
                base_name, ext = os.path.splitext(filename)
                if base_name.lower() == student_id.lower() and ext.lower() in all_formats:
                    known_image_path = os.path.join(known_faces_dir, filename)
                    break

    if not known_image_path:
        print(f"[FACE] No known face photo found for student: {student_id}")
        return False


    # 2. Load the student's known face encoding
    known_image = load_image_for_face(known_image_path)
    if known_image is None:
        print(f"[FACE] Could not load known face photo for student: {student_id}")
        return False

    try:
        known_encodings = face_recognition.face_encodings(known_image)
    except Exception as e:
        print(f"[FACE] Error getting known face encoding for student {student_id}: {e}")
        return False

    if not known_encodings:
        print(f"[FACE] No face found in known face photo for student: {student_id}")
        return False
    student_encoding = known_encodings[0]

    # 3. Load the uploaded image and find all face encodings in it
    uploaded_image = load_image_for_face(image_path)
    if uploaded_image is None:
        print(f"[FACE] Could not load uploaded image: {image_path}")
        return False

    try:
        face_locations = face_recognition.face_locations(uploaded_image)
    except Exception as e:
        print(f"[FACE] Error finding face locations in uploaded image: {e}")
        return False

    if not face_locations:
        print(f"[FACE] No faces found in uploaded image")
        return False

    try:
        uploaded_encodings = face_recognition.face_encodings(uploaded_image, face_locations)
    except Exception as e:
        print(f"[FACE] Error getting face encodings in uploaded image: {e}")
        return False

    # 4. Compare all uploaded faces against the student's encoding
    # compare_faces expects (list_of_known_encodings, single_face_to_check, tolerance)
    # We iterate over each face found in the uploaded image and check if it matches the student
    MATCH_TOLERANCE = 0.5  # Stricter than default 0.6 to reduce false positives
    for uploaded_encoding in uploaded_encodings:
        face_distance = face_recognition.face_distance([student_encoding], uploaded_encoding)[0]
        is_match = face_recognition.compare_faces(
            [student_encoding], uploaded_encoding, tolerance=MATCH_TOLERANCE
        )
        print(f"[FACE] Distance: {face_distance:.4f}, Match: {is_match[0]}")
        if is_match[0]:
            print(f"[FACE] Student {student_id} VERIFIED OK (distance={face_distance:.4f})")
            return True

    print(f"[FACE] Student {student_id} NOT verified")
    return False