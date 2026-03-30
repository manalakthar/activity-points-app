# Activity Points Tracker App
A web application for St Joseph Engineering College to track and manage 
AICTE Student Activity Points (SAP) for B.E./B.Tech students.

## What this app does
- Students register, upload certificates, and track their activity points
- Faculty mentors verify and approve submissions
- Departmental coordinators review approved submissions
- College SAP coordinator gives final approval
- Points are automatically added to student profiles upon approval

## Tech Stack
- **Backend:** Python, Flask
- **Database:** SQLite
- **OCR:** Tesseract + pytesseract
- **Face Recognition:** face_recognition library
- **Frontend:** HTML, CSS, JavaScript

## Team
| Person | Responsibility |
|---|---|
| Person 1 | Database + Flask routes (app.py) |
| Person 2 | Frontend (templates + static) |
| Person 3 | OCR + Face Recognition (modules/) |
| Person 4 | Integration + Testing |

---

## Setup Instructions (do this once)

### Step 1 — Install Tesseract (OCR engine)
Download and install from:
https://github.com/UB-Mannheim/tesseract/wiki

After installing, add to PATH:
```
C:\Program Files\Tesseract-OCR
```

Verify it works:
```bash
tesseract --version
```

### Step 2 — Install Poppler (PDF support)
Download from:
https://github.com/oschwartz10612/poppler-windows/releases

Extract and add to PATH:
```
C:\path\to\poppler\Library\bin
```

Verify it works:
```bash
pdftoppm -v
```

### Step 3 — Clone the project
```bash
git clone <your-repo-url>
cd activity-points-app
```

### Step 4 — Create and activate virtual environment
```bash
python -m venv venv
venv\Scripts\activate
```

### Step 5 — Install setuptools FIRST (important!)
```bash
pip install setuptools==69.5.1
```

### Step 6 — Install all libraries
```bash
pip install -r requirements.txt
```

### Step 7 — Run the app
```bash
python app.py
```

Then open your browser and go to:
```
http://127.0.0.1:5000
```

---

## Common Issues & Fixes

### face_recognition install fails
Make sure you installed setuptools first:
```bash
pip install setuptools==69.5.1
pip install -r requirements.txt
```

### Tesseract not found error
Add this to config.py:
```python
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### PDF upload not working
Make sure Poppler is installed and added to PATH correctly.
Restart VS Code after adding to PATH.

---

## Activity Points Policy
- Regular students: 100 points over 4 years
- Lateral entry students: 75 points over 3 years
- Suggested target: 12-15 points per semester

### Activity Categories
| Category | Participant Points | Organizer Points |
|---|---|---|
| Societal & Community | 10 | 20 |
| Technical & Innovation | 10 | 20 |
| Leadership & Professional | 5-10 | 10 |
| Sports, Arts & Wellness | 5 | 10 |
| Special/National Initiatives | 5 | 10 |