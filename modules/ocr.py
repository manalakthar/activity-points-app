import cv2
import pytesseract
import numpy as np
import os
import sys

# Add parent directory to path so we can import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def load_image(image_path):
    """
    Load any image type — jpg, jpeg, png, or pdf.
    """
    extension = os.path.splitext(image_path)[1].lower()

    if extension == '.pdf':
        try:
            from pdf2image import convert_from_path
            pages = convert_from_path(image_path)
            img = cv2.cvtColor(np.array(pages[0]), cv2.COLOR_RGB2BGR)
            print(f"Loaded PDF: {image_path}")
            return img
        except Exception as e:
            print(f"PDF load error: {e}")
            return None

    elif extension in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
        img = cv2.imread(image_path)
        print(f"Loaded image: {image_path}")
        return img

    else:
        print(f"Unsupported file type: {extension}")
        return None


def preprocess_image(img):
    """
    Clean up image for better OCR accuracy.
    """
    if img is None:
        return None

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Resize to make text bigger and clearer
    scale = 2
    resized = cv2.resize(
        gray, None, fx=scale, fy=scale,
        interpolation=cv2.INTER_CUBIC
    )

    # Remove noise
    blurred = cv2.GaussianBlur(resized, (5, 5), 0)

    # Make text pure black, background pure white
    _, thresh = cv2.threshold(
        blurred, 0, 255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    return thresh


def extract_text(image_path):
    """
    Extract all text from any image or PDF.
    Returns extracted text as a string.
    Used in app.py when student uploads a certificate.
    """
    print(f"\n[OCR] Processing: {image_path}")

    # Load the file
    img = load_image(image_path)
    if img is None:
        print("[OCR] Failed to load image")
        return ""

    # Preprocess it
    cleaned = preprocess_image(img)
    if cleaned is None:
        print("[OCR] Failed to preprocess image")
        return ""

    # Extract text
    # --psm 6 = treat as a block of text (good for certificates)
    ocr_config = '--psm 6'
    text = pytesseract.image_to_string(cleaned, config=ocr_config)

    extracted = text.strip()
    print(f"[OCR] Extracted {len(extracted)} characters")
    return extracted