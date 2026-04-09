# Activity Points Tracker

A web application for St Joseph Engineering College to track and manage 
AICTE Student Activity Points (SAP) for B.E./B.Tech students.

## About the Project
This app digitizes the entire SAP process — students upload certificates, 
faculty mentors verify them, coordinators approve them, and points are 
automatically added to student profiles. Built with Python, Flask, SQLite, 
OCR, and Face Recognition.

## Tech Stack
- **Backend:** Python, Flask
- **Database:** SQLite
- **OCR:** Tesseract + pytesseract
- **Face Recognition:** face_recognition library
- **Frontend:** HTML, CSS, JavaScript

## Team
| Person | Responsibility |
|---|---|
| Person 1 | Database + Flask routes (app.py, database.py) |
| Person 2 | Frontend (templates/, static/) |
| Person 3 | OCR + Face Recognition (modules/) |
| Person 4 | Integration + Testing |

---

###  Install Poppler (for PDF support)
Download from:
https://github.com/oschwartz10612/poppler-windows/releases

Extract and add the bin folder to your system PATH:
```
C:\path\to\poppler\Library\bin
```
Verify:
```bash
pdftoppm -v
```


```

### Activate virtual environment
```bash
venv\Scripts\activate
```
You should see `(venv)` in your terminal ✅

##  Every Time You Start Coding

Open your project in VS Code, then run these commands in order:

# Step 1 - Activate virtual environment
venv\Scripts\activate

# Step 2 - Pull latest changes from GitHub
git pull

# Step 3 - Run the app
python app.py

# Step 4 - Open in browser
http://127.0.0.1:5000
```

---

## Every Time You Finish Coding
```bash
# Step 1 - Stop the running server
Ctrl + C

# Step 2 - Add all your changes
git add .

# Step 3 - Save changes with a message describing what you did
git commit -m "describe what you did here"

# Step 4 - Push to GitHub
git push
```

---

##  Important Rules for the Team
```
1. Always git pull before you start coding
2. Always git push when you finish coding
3. Never push broken code — test before pushing
4. Always activate venv before running anything
5. Never commit database.db — it's in .gitignore
```

----

## 📋 Activity Points Policy Summary

| Student Type | Points Required |
|---|---|
| Regular (4 years) | 100 points |
| Lateral Entry (3 years) | 75 points |

| Category | Participant | Organizer |
|---|---|---|
| Societal & Community | 10 | 20 |
| Technical & Innovation | 10 | 20 |
| Leadership & Professional | 5-10 | 10 |
| Sports, Arts & Wellness | 5 | 10 |
| Special/National Initiatives | 5 | 10 |

---

## 📁 Project Structure
```
activity-points-app/
├── modules/
│   ├── face_auth.py        ← Face recognition
│   └── ocr.py              ← OCR text extraction
├── static/
│   ├── style.css           ← Styles
│   └── script.js           ← JavaScript
├── templates/              ← All HTML pages
├── known_faces/            ← Student reference photos
├── uploads/                ← Uploaded certificates
├── app.py                  ← Main Flask app
├── config.py               ← Configuration
├── database.py             ← Database setup
└── requirements.txt        ← All libraries
```
