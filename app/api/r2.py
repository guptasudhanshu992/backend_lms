from fastapi import APIRouter, File, UploadFile, HTTPException
from app.services.r2_service import upload_fileobj
import aiofiles

router = APIRouter()


@router.post("/r2/upload")
async def upload_to_r2(file: UploadFile = File(...)):
    # read into memory stream (small demo). For production, stream to disk or S3 multipart.
    try:
        contents = await file.read()
        key, url = upload_fileobj(contents, filename=file.filename)
        return {"key": key, "url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
