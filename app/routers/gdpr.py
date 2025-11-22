"""
GDPR-related routes for data portability and erasure.
"""
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.core.dependencies import get_current_user
from app.services.gdpr_service import gdpr_service

router = APIRouter()


@router.get('/export')
async def export_my_data(current_user: dict = Depends(get_current_user)):
    """
    Export all user data (GDPR Article 20 - Right to Data Portability).
    Returns comprehensive JSON with user info, sessions, audit logs.
    """
    user_id = current_user["id"]
    data = await gdpr_service.export_user_data(user_id)
    
    return JSONResponse(
        content=data,
        headers={
            "Content-Disposition": f"attachment; filename=user_data_{user_id}.json"
        }
    )


@router.post('/delete-account')
async def delete_my_account(current_user: dict = Depends(get_current_user)):
    """
    Delete own account (GDPR Article 17 - Right to Erasure).
    Performs soft delete (anonymization) by default.
    """
    user_id = current_user["id"]
    result = await gdpr_service.delete_user_account(user_id, hard_delete=False)
    
    return result


@router.get('/consent')
async def get_my_consent(current_user: dict = Depends(get_current_user)):
    """Get current consent status."""
    user_id = current_user["id"]
    consent = await gdpr_service.get_consent_status(user_id)
    return consent


@router.post('/consent')
async def update_my_consent(
    consent: bool,
    current_user: dict = Depends(get_current_user),
):
    """Update consent status."""
    user_id = current_user["id"]
    result = await gdpr_service.update_consent(user_id, consent)
    return result
