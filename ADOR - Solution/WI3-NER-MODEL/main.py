# main.py
# FastAPI application — upload a DOCX and get extracted entities back

import shutil
import tempfile
from pathlib import Path

from fastapi           import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

from parser import parse_docx

app = FastAPI(
    title       = "ADOR — Rule-Based NER API",
    description = "Extract financial named entities from DOCX term sheets",
    version     = "1.0.0",
)


@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    if not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only .docx files are supported")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        result = parse_docx(tmp_path)
        result["source"] = file.filename
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        Path(tmp_path).unlink(missing_ok=True)
