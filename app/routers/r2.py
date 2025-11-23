from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from app.services.r2_service import upload_fileobj
from app.core.dependencies import require_admin

router = APIRouter()

@router.post('/upload', dependencies=[Depends(require_admin)])
def upload_image(file: UploadFile = File(...)):
    try:
        key, url = upload_fileobj(file.file, filename=file.filename)
        return {"key": key, "url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
