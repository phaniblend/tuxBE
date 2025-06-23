import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class SessionService:
    """
    Session management service for persisting user data
    MVP implementation using local JSON files
    Can be upgraded to database storage later
    """
    
    def __init__(self):
        # Create sessions directory if it doesn't exist
        self.sessions_dir = Path("sessions")
        self.sessions_dir.mkdir(exist_ok=True)
        
        # Session metadata file
        self.metadata_file = self.sessions_dir / "sessions_metadata.json"
        self._ensure_metadata_file()
    
    def _ensure_metadata_file(self):
        """Ensure metadata file exists"""
        if not self.metadata_file.exists():
            with open(self.metadata_file, 'w') as f:
                json.dump({"sessions": {}}, f)
    
    async def create_session(self, data: Dict[str, Any]) -> str:
        """
        Create a new session and save data
        
        Args:
            data: Session data to save
            
        Returns:
            Session ID
        """
        try:
            session_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()
            
            # Prepare session data
            session_data = {
                "id": session_id,
                "created_at": timestamp,
                "updated_at": timestamp,
                "data": data
            }
            
            # Save session file
            session_file = self.sessions_dir / f"{session_id}.json"
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            # Update metadata
            await self._update_metadata(session_id, {
                "created_at": timestamp,
                "updated_at": timestamp,
                "app_idea": data.get("requirements", {}).get("purpose", "Untitled Project")
            })
            
            logger.info(f"Created session: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to create session: {str(e)}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session data by ID
        
        Args:
            session_id: Session ID
            
        Returns:
            Session data or None if not found
        """
        try:
            session_file = self.sessions_dir / f"{session_id}.json"
            
            if not session_file.exists():
                logger.warning(f"Session not found: {session_id}")
                return None
            
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            return session_data
            
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {str(e)}")
            return None
    
    async def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """
        Update existing session data
        
        Args:
            session_id: Session ID
            data: Updated session data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session_file = self.sessions_dir / f"{session_id}.json"
            
            if not session_file.exists():
                logger.warning(f"Session not found for update: {session_id}")
                return False
            
            # Load existing session
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            # Update data
            session_data["updated_at"] = datetime.now().isoformat()
            session_data["data"] = data
            
            # Save updated session
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            # Update metadata
            await self._update_metadata(session_id, {
                "updated_at": session_data["updated_at"],
                "app_idea": data.get("requirements", {}).get("purpose", session_data.get("data", {}).get("requirements", {}).get("purpose", "Untitled Project"))
            })
            
            logger.info(f"Updated session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update session {session_id}: {str(e)}")
            return False
    
    async def list_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        List recent sessions
        
        Args:
            limit: Maximum number of sessions to return
            
        Returns:
            List of session metadata
        """
        try:
            with open(self.metadata_file, 'r') as f:
                metadata = json.load(f)
            
            sessions = []
            for session_id, info in metadata.get("sessions", {}).items():
                sessions.append({
                    "id": session_id,
                    "app_idea": info.get("app_idea", "Untitled Project"),
                    "created_at": info.get("created_at"),
                    "updated_at": info.get("updated_at")
                })
            
            # Sort by updated_at descending
            sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
            
            return sessions[:limit]
            
        except Exception as e:
            logger.error(f"Failed to list sessions: {str(e)}")
            return []
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session
        
        Args:
            session_id: Session ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session_file = self.sessions_dir / f"{session_id}.json"
            
            if session_file.exists():
                session_file.unlink()
                
            # Remove from metadata
            await self._remove_from_metadata(session_id)
            
            logger.info(f"Deleted session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {str(e)}")
            return False
    
    async def _update_metadata(self, session_id: str, info: Dict[str, Any]):
        """Update session metadata"""
        try:
            with open(self.metadata_file, 'r') as f:
                metadata = json.load(f)
            
            if "sessions" not in metadata:
                metadata["sessions"] = {}
            
            metadata["sessions"][session_id] = info
            
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to update metadata: {str(e)}")
    
    async def _remove_from_metadata(self, session_id: str):
        """Remove session from metadata"""
        try:
            with open(self.metadata_file, 'r') as f:
                metadata = json.load(f)
            
            if "sessions" in metadata and session_id in metadata["sessions"]:
                del metadata["sessions"][session_id]
                
                with open(self.metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
                    
        except Exception as e:
            logger.error(f"Failed to remove from metadata: {str(e)}")
    
    async def export_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Export session data for download
        
        Args:
            session_id: Session ID
            
        Returns:
            Session data with export metadata
        """
        try:
            session_data = await self.get_session(session_id)
            
            if not session_data:
                return None
            
            # Add export metadata
            export_data = {
                "export_version": "1.0",
                "exported_at": datetime.now().isoformat(),
                "session": session_data
            }
            
            return export_data
            
        except Exception as e:
            logger.error(f"Failed to export session {session_id}: {str(e)}")
            return None
    
    async def import_session(self, export_data: Dict[str, Any]) -> Optional[str]:
        """
        Import session from exported data
        
        Args:
            export_data: Exported session data
            
        Returns:
            New session ID or None if failed
        """
        try:
            if "session" not in export_data:
                logger.error("Invalid export data: missing session")
                return None
            
            session_data = export_data["session"]["data"]
            new_session_id = await self.create_session(session_data)
            
            return new_session_id
            
        except Exception as e:
            logger.error(f"Failed to import session: {str(e)}")
            return None 