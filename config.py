import pytesseract

# Tesseract path for Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Folders
KNOWN_FACES_DIR = 'known_faces'
UPLOAD_DIR = 'uploads'

# Points required
REGULAR_STUDENT_POINTS = 100
LATERAL_ENTRY_POINTS = 75

# Activity categories and points
ACTIVITY_POINTS = {
    'Societal & Community': {
        'participant': 10,
        'organizer': 20
    },
    'Technical & Innovation': {
        'participant': 10,
        'organizer': 20
    },
    'Leadership & Professional': {
        'participant': 5,
        'organizer': 10
    },
    'Sports, Arts & Wellness': {
        'participant': 5,
        'organizer': 10
    },
    'Special/National Initiatives': {
        'participant': 5,
        'organizer': 10
    }
}