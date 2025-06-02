from typing import List, Optional
from pydantic import BaseModel, Field

class RepeatableFieldMapping(BaseModel):
    """Model for mapping repeatable fields in a form"""
    field_name: str = Field(..., description="Name of the field in the client data")
    pdf_field_pattern: str = Field(..., description="Pattern for the PDF field ID, e.g., 'Pt3Line{index}a_EmployerName[0]'")
    field_type: str = Field(..., description="Type of field (text, date, etc.)")
    max_entries: int = Field(..., description="Maximum number of entries allowed")
    field_indices: Optional[List[int]] = Field(None, description="List of actual line numbers to use")
    supplemental_page_pattern: Optional[str] = Field(None, description="Pattern for supplemental page fields if needed")

    def get_pdf_field_name(self, index: int) -> str:
        """
        Get the PDF field name for a specific index.
        If field_indices is provided, use those specific line numbers instead of sequential indices.
        
        Args:
            index: The index of the entry (0-based)
            
        Returns:
            The formatted PDF field name
        """
        if self.field_indices and 0 <= index < len(self.field_indices):
            actual_index = self.field_indices[index]
        else:
            actual_index = index + 1  # Default to 1-based indexing
            
        return self.pdf_field_pattern.format(index=actual_index)

    def get_supplemental_field_name(self, index: int) -> Optional[str]:
        """Get the supplemental PDF field name for a specific index."""
        if not self.supplemental_page_pattern:
            return None
        return self.supplemental_page_pattern.format(index=index + 1)  # 1-based indexing for supplemental pages 