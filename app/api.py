from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

class DocumentPayload(BaseModel):
    documenttype: str
    document: str  # base64 encoded string
    documentid: str = None
import uuid
import base64
import os
import tempfile
from typing import Optional
import fitz  # PyMuPDF
from PIL import Image

def save_image(image: Image.Image, folder: str, filename: str) -> str:
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, filename)
    image.save(path)
    return path

def get_image_info(image: Image.Image, filename: str) -> dict:
    return {
        "image_name": filename,
        "image_size": image.size  # (width, height)
    }

router = APIRouter()

@router.post("/upload-document")
async def upload_document(payload: DocumentPayload):
    import time
    from io import BytesIO
    api_start = time.time()
    try:
        # Generate or use provided documentid
        documentid = payload.documentid or str(uuid.uuid4())
        file_bytes = base64.b64decode(payload.document)
        temp_dir = os.path.join(tempfile.gettempdir(), "ocr_ai_uploads")
        os.makedirs(temp_dir, exist_ok=True)



        service_start = time.time()
        # Try to detect if it's a PDF (by header)
        if file_bytes[:4] == b'%PDF':
            # Convert PDF to images using PyMuPDF (fitz)
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            saved_files = []
            image_infos = []
            for idx, page in enumerate(doc):
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                filename = f"{payload.documenttype}_page{idx+1}.png"
                path = save_image(img, temp_dir, filename)
                saved_files.append(path)
                image_infos.append(get_image_info(img, filename))
            service_time = time.time() - service_start
            api_time = time.time() - api_start
            return {
                "status": "success",
                "documentid": documentid,
                "saved_images": saved_files,
                "image_infos": image_infos,
                "service_time": service_time,
                "api_time": api_time
            }
        else:
            # Assume it's an image
            img = Image.open(BytesIO(file_bytes))
            filename = f"{payload.documenttype}_uploaded.png"
            path = save_image(img, temp_dir, filename)
            image_info = get_image_info(img, filename)
            service_time = time.time() - service_start
            api_time = time.time() - api_start
            return {
                "status": "success",
                "documentid": documentid,
                "saved_image": path,
                "image_info": image_info,
                "service_time": service_time,
                "api_time": api_time
            }
    except Exception as e:
        api_time = time.time() - api_start
        print(f"error: {e}")
        return JSONResponse(content={"status": "error", "detail": str(e), "api_time": api_time}, status_code=400)

@router.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}
