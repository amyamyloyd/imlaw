"""Test client profile model validation."""

import pytest
from src.models.client_profile import ClientProfile
from pydantic import ValidationError

def test_create_minimal_client_profile():
    """Test creating a client profile with minimum required fields."""
    profile_data = {
        "client_id": "test123",
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "phone": "+11234567890"
    }
    
    profile = ClientProfile(**profile_data)
    assert profile.client_id == "test123"
    assert profile.email == "test@example.com"
    assert profile.first_name == "John"
    assert profile.last_name == "Doe"
    assert profile.phone == "+11234567890"

def test_invalid_phone_number():
    """Test that invalid phone numbers are rejected."""
    profile_data = {
        "client_id": "test123",
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "phone": "123"  # Too short
    }
    
    with pytest.raises(ValidationError) as exc_info:
        ClientProfile(**profile_data)
    
    assert "Invalid phone number format" in str(exc_info.value) 