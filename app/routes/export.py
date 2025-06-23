from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging

from app.services.export_service import ExportService

logger = logging.getLogger(__name__)
router = APIRouter()
export_service = ExportService()

class ExportRequest(BaseModel):
    screens: List[Dict[str, Any]]
    project_name: Optional[str] = "TUX Project"
    ux_specs: Optional[Dict[str, Any]] = None
    requirements: Optional[Dict[str, Any]] = None

class SingleScreenExportRequest(BaseModel):
    screen: Dict[str, Any]

@router.post("/export/html")
async def export_html(request: ExportRequest):
    """Export screens as HTML document"""
    try:
        html_content = await export_service.export_screens_html(
            screens=request.screens,
            project_name=request.project_name
        )
        
        # Save file and return download link
        file_path = await export_service.save_export(
            content=html_content,
            filename=request.project_name.replace(' ', '_'),
            format="html"
        )
        
        return FileResponse(
            path=file_path,
            media_type="text/html",
            filename=f"{request.project_name}_export.html"
        )
        
    except Exception as e:
        logger.error(f"Failed to export HTML: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export/json")
async def export_json(request: ExportRequest):
    """Export complete project data as JSON"""
    try:
        json_content = await export_service.export_screens_json(
            screens=request.screens,
            ux_specs=request.ux_specs,
            requirements=request.requirements
        )
        
        # Save file and return download link
        file_path = await export_service.save_export(
            content=json_content,
            filename=request.project_name.replace(' ', '_'),
            format="json"
        )
        
        return FileResponse(
            path=file_path,
            media_type="application/json",
            filename=f"{request.project_name}_export.json"
        )
        
    except Exception as e:
        logger.error(f"Failed to export JSON: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export/svg")
async def export_svg(request: SingleScreenExportRequest):
    """Export a single screen as SVG"""
    try:
        svg_content = await export_service.export_screen_svg(
            screen=request.screen
        )
        
        screen_name = request.screen.get('name', 'screen').replace(' ', '_')
        
        # Save file and return download link
        file_path = await export_service.save_export(
            content=svg_content,
            filename=screen_name,
            format="svg"
        )
        
        return FileResponse(
            path=file_path,
            media_type="image/svg+xml",
            filename=f"{screen_name}_export.svg"
        )
        
    except Exception as e:
        logger.error(f"Failed to export SVG: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export/html/inline")
async def export_html_inline(request: ExportRequest):
    """Export screens as HTML (return content directly, not as file)"""
    try:
        html_content = await export_service.export_screens_html(
            screens=request.screens,
            project_name=request.project_name
        )
        
        return Response(
            content=html_content,
            media_type="text/html",
            headers={
                "Content-Disposition": f"inline; filename={request.project_name}_export.html"
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to export HTML inline: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export/json/inline")
async def export_json_inline(request: ExportRequest):
    """Export project data as JSON (return content directly)"""
    try:
        json_content = await export_service.export_screens_json(
            screens=request.screens,
            ux_specs=request.ux_specs,
            requirements=request.requirements
        )
        
        return Response(
            content=json_content,
            media_type="application/json",
            headers={
                "Content-Disposition": f"inline; filename={request.project_name}_export.json"
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to export JSON inline: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export/svg/inline")
async def export_svg_inline(request: SingleScreenExportRequest):
    """Export screen as SVG (return content directly)"""
    try:
        svg_content = await export_service.export_screen_svg(
            screen=request.screen
        )
        
        return Response(
            content=svg_content,
            media_type="image/svg+xml",
            headers={
                "Content-Disposition": f"inline; filename=screen_export.svg"
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to export SVG inline: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 