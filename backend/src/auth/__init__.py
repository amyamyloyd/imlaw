"""Authentication module for user management and access control"""

from .dependencies import User, get_current_user

__all__ = ["User", "get_current_user"] 