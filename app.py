from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from flask_cors import CORS
import os
from services.document_service import validate_document
from transformers import pipeline
import PyPDF2
import docx
from PIL import Image
import pytesseract
import re

# Initialize app
app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load Hugging Face summarizer once
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# Allowed image extensions
ALLOWED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".tiff", ".bmp"}

def extract_text(file_path):
    """Extract text from txt, pdf, docx, or image"""
    text = ""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

    elif ext == ".pdf":
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""

    elif ext == ".docx":
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"

    elif ext in ALLOWED_IMAGE_EXT:
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)

    return text.strip()

def extract_key_info(text):
    """Extract Name, DOB, Institution, Place, Date & Time using regex"""
    info = {}

    # These patterns can be adjusted for your documents
    name_pattern = r"Name\s*[:\-]\s*(.*)"
    dob_pattern = r"(Date of Birth|DOB)\s*[:\-]\s*(\d{2}[\/\-]\d{2}[\/\-]\d{4})"
    institution_pattern = r"(Institution|College|University)\s*[:\-]\s*(.*)"
    place_pattern = r"(Place)\s*[:\-]\s*(.*)"
    datetime_pattern = r"(Date\s*[:\-]\s*\d{2}[\/\-]\d{2}[\/\-]\d{4}.*Time\s*[:\-]\s*\d{2}:\d{2})"

    name_match = re.search(name_pattern, text, re.IGNORECASE)
    dob_match = re.search(dob_pattern, text, re.IGNORECASE)
    institution_match = re.search(institution_pattern, text, re.IGNORECASE)
    place_match = re.search(place_pattern, text, re.IGNORECASE)
    datetime_match = re.search(datetime_pattern, text, re.IGNORECASE)

    info["Name"] = name_match.group(1).strip() if name_match else None
    info["DOB"] = dob_match.group(2).strip() if dob_match else None
    info["Institution"] = institution_match.group(2).strip() if institution_match else None
    info["Place"] = place_match.group(2).strip() if place_match else None
    info["DateTime"] = datetime_match.group(1).strip() if datetime_match else None

    return info

@app.route("/")
def home():
    return "✅ AI Document Validation Backend is Running!"

@app.route("/validate", methods=["POST"])
def validate():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No filename provided"}), 400

        # Save uploaded file
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
        file.save(file_path)

        # 1️⃣ Call your existing validation function
        result = validate_document(file_path)

        # 2️⃣ Extract text
        text = extract_text(file_path)

        # 3️⃣ Extract key info
        key_info = extract_key_info(text)
        result["key_info"] = key_info

        # 4️⃣ Summarize
        summary_text = "⚠️ No readable text found."
        if text:
            if len(text) > 1000:
                text = text[:1000]
            try:
                summary = summarizer(text, max_length=120, min_length=30, do_sample=False)
                summary_text = summary[0]["summary_text"]
            except:
                summary_text = "⚠️ Could not generate summary."
        result["summary"] = summary_text

        return jsonify(result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
