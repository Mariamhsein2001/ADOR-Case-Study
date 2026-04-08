# ADOR — Rule-Based NER API

A FastAPI-based service for extracting financial named entities from `.docx` term sheets using a rule-based parser.

---

## 📌 Overview

This project provides an API that:

* Accepts `.docx` files
* Extracts structured financial entities from tables
* Applies fuzzy matching for robustness
* Validates extracted fields against a schema

Core components:

* API layer → 
* Parsing logic → 
* Field mapping & fuzzy matching → 

---

## 📁 Project Structure

```
project/
│── main.py        # FastAPI app
│── parser.py      # Core extraction logic
│── fields.py      # Entity mappings + fuzzy matching
│── schema.py      # Validation rules (required)
│── README.md
```

---

## ⚙️ Requirements

* Python 3.9+
* pip

---

## 📦 Installation

1. Clone the repository or download files

2. Create a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows
```

3. Install dependencies:

```bash
cd ADOR-Case-Study/ADOR-Solution/WI2-Rule-based-NER
pip install -r requirements.txt
```

---

## ▶️ Running the Application

### Option 1: Run with Uvicorn (recommended)

```bash
uvicorn main:app --reload
```

### Option 2: Run as a Python script

```bash
python main.py
```

The server will start at:

```
http://127.0.0.1:8000
```

---

## 📖 API Documentation

Once the server is running, open:

* Swagger UI:

```
http://127.0.0.1:8000/docs
```

---

## 📤 API Usage

### Endpoint

```
POST /extract
```

### Request

* Content-Type: `multipart/form-data`
* Body:

  * `file`: `.docx` file

### Example (curl)

```bash
curl -X POST "http://127.0.0.1:8000/extract" \
-F "file=@sample.docx"
```

---

## 📥 Response Example

```json
{
  "source": "sample.docx",
  "engine": "rule_based_parser",
  "document_type": "term_sheet_docx",
  "entities": {
    "Counterparty": "ABC Bank",
    "Notional": "1000000",
    "Maturity": "2026-12-31"
  },
  "errors": []
}
```

---

## 🧠 How It Works

### 1. Extraction

* Reads tables from `.docx`
* Matches keys (left column) to known labels

### 2. Fuzzy Matching

* Uses Levenshtein distance to handle typos
* Example: `"party a"` → `"Counterparty"`

### 3. Validation

* Applies regex rules from `schema.py`
* Flags missing or invalid fields

---

## 🎯 Target Entities

The system extracts the following:

* Counterparty
* Initial Valuation Date
* Notional
* Valuation Date
* Maturity
* Underlying
* Coupon
* Barrier
* Calendar

---

## Error Handling

* Non-DOCX file → `400 Bad Request`
* Parsing failure → `500 Internal Server Error`
* Validation issues → returned in `"errors"` field

---
