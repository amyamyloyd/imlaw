"""Save Progress Service.

This service handles partial save and resume functionality for client profiles, including:
- Progress tracking per section
- Last edited field tracking
- Validation error tracking
- Completion percentage calculation
- Resume state management

The service integrates with MongoDB for efficient state persistence.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from bson import ObjectId
from src.db.database import Database
from src.models.client_profile import SaveProgress, ClientProfile

class SaveProgressService:
    """Service for managing partial save and resume functionality."""
    
    def __init__(self):
        """Initialize service with MongoDB connection."""
        database = Database()
        self.db = database.db
        self.clients_collection = self.db['client_profiles']
    
    async def save_progress(
        self,
        client_id: str,
        section: str,
        field: str,
        validation_errors: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[bool, Optional[str]]:
        """Save current progress for a client profile.
        
        Args:
            client_id: ID of the client profile
            section: Current section being edited
            field: Current field being edited
            validation_errors: List of validation errors if any
            
        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
            
        Example:
            success, error = await service.save_progress(
                "client123",
                "employment",
                "employer",
                [{"field": "start_date", "error": "Invalid date format"}]
            )
        """
        try:
            # Update save progress
            update_result = await self.clients_collection.update_one(
                {"client_id": client_id},
                {
                    "$set": {
                        "save_progress.last_section": section,
                        "save_progress.last_field": field,
                        "save_progress.last_saved": datetime.utcnow(),
                        "save_progress.validation_errors": validation_errors or [],
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return update_result.modified_count > 0, None
            
        except Exception as e:
            return False, str(e)
    
    async def get_resume_state(
        self,
        client_id: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Get the saved state to resume editing.
        
        Args:
            client_id: ID of the client profile
            
        Returns:
            Tuple[Optional[Dict[str, Any]], Optional[str]]: (resume_state, error_message)
            
        Example:
            state, error = await service.get_resume_state("client123")
            if state:
                section = state["last_section"]
                field = state["last_field"]
        """
        try:
            result = await self.clients_collection.find_one(
                {"client_id": client_id},
                {"save_progress": 1}
            )
            
            if not result or "save_progress" not in result:
                return None, "Save progress not found"
                
            return result["save_progress"], None
            
        except Exception as e:
            return None, str(e)
    
    async def update_completion_percentage(
        self,
        client_id: str
    ) -> Tuple[float, Optional[str]]:
        """Calculate and update completion percentage.
        
        Args:
            client_id: ID of the client profile
            
        Returns:
            Tuple[float, Optional[str]]: (completion_percentage, error_message)
            
        Example:
            percentage, error = await service.update_completion_percentage("client123")
            if percentage >= 100:
                print("Profile complete!")
        """
        try:
            # Get client profile
            result = await self.clients_collection.find_one(
                {"client_id": client_id}
            )
            
            if not result:
                return 0.0, "Client not found"
                
            # Create ClientProfile instance for calculation
            profile = ClientProfile(**result)
            profile.update_completion_status()
            
            # Update in database
            await self.clients_collection.update_one(
                {"client_id": client_id},
                {
                    "$set": {
                        "save_progress.completion_percentage": profile.save_progress.completion_percentage,
                        "is_complete": profile.is_complete,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return profile.save_progress.completion_percentage, None
            
        except Exception as e:
            return 0.0, str(e)
    
    async def clear_validation_errors(
        self,
        client_id: str,
        section: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """Clear validation errors for a client profile.
        
        Args:
            client_id: ID of the client profile
            section: Optional section to clear errors for. If None, clears all errors.
            
        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
            
        Example:
            success, error = await service.clear_validation_errors(
                "client123",
                "employment"
            )
        """
        try:
            if section:
                # Clear errors for specific section
                update_result = await self.clients_collection.update_one(
                    {"client_id": client_id},
                    {
                        "$pull": {
                            "save_progress.validation_errors": {
                                "section": section
                            }
                        },
                        "$set": {"updated_at": datetime.utcnow()}
                    }
                )
            else:
                # Clear all errors
                update_result = await self.clients_collection.update_one(
                    {"client_id": client_id},
                    {
                        "$set": {
                            "save_progress.validation_errors": [],
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
            
            return update_result.modified_count > 0, None
            
        except Exception as e:
            return False, str(e)
    
    async def get_validation_errors(
        self,
        client_id: str,
        section: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Get validation errors for a client profile.
        
        Args:
            client_id: ID of the client profile
            section: Optional section to get errors for. If None, gets all errors.
            
        Returns:
            Tuple[List[Dict[str, Any]], Optional[str]]: (validation_errors, error_message)
            
        Example:
            errors, error = await service.get_validation_errors(
                "client123",
                "employment"
            )
        """
        try:
            result = await self.clients_collection.find_one(
                {"client_id": client_id},
                {"save_progress.validation_errors": 1}
            )
            
            if not result or "save_progress" not in result:
                return [], "Save progress not found"
                
            errors = result["save_progress"].get("validation_errors", [])
            
            if section:
                errors = [e for e in errors if e.get("section") == section]
                
            return errors, None
            
        except Exception as e:
            return [], str(e) 