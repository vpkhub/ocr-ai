from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import base64
import os
import tempfile
from typing import Optional
from PIL import Image
import fitz  # PyMuPDF

router = APIRouter()

class DocumentPayload(BaseModel):
    documenttype: str
    document: str  # base64 encoded string

def save_image(image: Image.Image, folder: str, filename: str) -> str:
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, filename)
    image.save(path)
    return path

@router.get("/ping")
def ping():
    return JSONResponse(content={"message": "pong"})

@router.post("/upload-document")
async def upload_document(payload: DocumentPayload):
    try:
        file_bytes = base64.b64decode(payload.document)
        temp_dir = os.path.join(tempfile.gettempdir(), "ocr_ai_uploads")
        os.makedirs(temp_dir, exist_ok=True)

        # Try to detect if it's a PDF (by header)
        if file_bytes[:4] == b'%PDF':
            # Convert PDF to images using PyMuPDF (fitz)
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            saved_files = []
            for idx, page in enumerate(doc):
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                filename = f"{payload.documenttype}_page{idx+1}.png"
                path = save_image(img, temp_dir, filename)
                saved_files.append(path)
            return {"status": "success", "saved_images": saved_files}
        else:
            # Assume it's an image
            from io import BytesIO
            img = Image.open(BytesIO(file_bytes))
            filename = f"{payload.documenttype}_uploaded.png"
            path = save_image(img, temp_dir, filename)
            return {"status": "success", "saved_image": path}
    except Exception as e:
        return JSONResponse(content={"status": "error", "detail": str(e)}, status_code=400)
