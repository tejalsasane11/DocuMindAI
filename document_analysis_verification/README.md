# Multimodal AI for Intelligent Document Analysis and Verification

A beginner-friendly, local Streamlit application that accepts PDF and image documents, extracts text using OCR, identifies useful fields, applies explainable rule-based checks, and creates downloadable reports.

The project does **not** use paid APIs or claim legal document authenticity. It reports only the checks implemented in the application.

## Requirements

- Windows 10 or 11
- Python 3.11 or 3.12 recommended
- Tesseract OCR installed at `C:\Program Files\Tesseract-OCR`

## Windows Setup

Open PowerShell in this project directory:

```powershell
cd C:\Users\laptop\OneDrive\Desktop\DocuMindAI\document_analysis_verification
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks virtual-environment activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Run the application

After setup is completed:

```powershell
streamlit run app.py
```

Open the local address shown by Streamlit, usually `http://localhost:8501`.

## Project folders

- `modules/`: Modular processing components
- `sample_documents/`: Optional test documents
- `reports/`: Generated reports
- `assets/`: Images and visual resources
