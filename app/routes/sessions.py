from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging

from app.services.session_service import SessionService

logger = logging.getLogger(__name__)
router = APIRouter()
session_service = SessionService()

class SessionCreateRequest(BaseModel):
    requirements: Dict[str, Any]
    ux_specs: Optional[Dict[str, Any]] = None
    screens: Optional[List[Dict[str, Any]]] = None

class SessionUpdateRequest(BaseModel):
    requirements: Optional[Dict[str, Any]] = None
    ux_specs: Optional[Dict[str, Any]] = None
    screens: Optional[List[Dict[str, Any]]] = None

class SessionResponse(BaseModel):
    id: str
    created_at: str
    updated_at: str
    data: Dict[str, Any]

class SessionListItem(BaseModel):
    id: str
    app_idea: str
    created_at: str
    updated_at: str

@router.post("/sessions")
async def create_session(request: SessionCreateRequest):
    """Create a new session to save user progress"""
    try:
        data = {
            "requirements": request.requirements,
            "ux_specs": request.ux_specs,
            "screens": request.screens
        }
        
        session_id = await session_service.create_session(data)
        
        return {
            "session_id": session_id,
            "message": "Session created successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to create session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Retrieve a saved session"""
    try:
        session_data = await session_service.get_session(session_id)
        
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return session_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/sessions/{session_id}")
async def update_session(session_id: str, request: SessionUpdateRequest):
    """Update an existing session"""
    try:
        # Get existing session
        existing_session = await session_service.get_session(session_id)
        if not existing_session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Merge updates with existing data
        updated_data = existing_session["data"].copy()
        
        if request.requirements is not None:
            updated_data["requirements"] = request.requirements
        if request.ux_specs is not None:
            updated_data["ux_specs"] = request.ux_specs
        if request.screens is not None:
            updated_data["screens"] = request.screens
        
        # Update session
        success = await session_service.update_session(session_id, updated_data)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update session")
        
        return {
            "session_id": session_id,
            "message": "Session updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions")
async def list_sessions(limit: int = 10):
    """List recent sessions"""
    try:
        sessions = await session_service.list_sessions(limit=limit)
        return {
            "sessions": sessions,
            "total": len(sessions)
        }
        
    except Exception as e:
        logger.error(f"Failed to list sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session"""
    try:
        success = await session_service.delete_session(session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "message": "Session deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}/export")
async def export_session(session_id: str):
    """Export session data for download"""
    try:
        export_data = await session_service.export_session(session_id)
        
        if not export_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return export_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sessions/import")
async def import_session(export_data: Dict[str, Any]):
    """Import a previously exported session"""
    try:
        new_session_id = await session_service.import_session(export_data)
        
        if not new_session_id:
            raise HTTPException(status_code=400, detail="Invalid export data")
        
        return {
            "session_id": new_session_id,
            "message": "Session imported successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to import session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 