"""Permission and authorization service."""

from functools import wraps
from typing import Callable
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from supervisor.models.membership import Membership
from supervisor.models.user import User
from supervisor.services.rdmp_service import get_current_rdmp


def get_user_permissions(db: Session, user_id: int, project_id: int) -> dict[str, bool]:
    """Get user's permissions for a project based on RDMP role."""
    # Check membership
    membership = (
        db.query(Membership)
        .filter(Membership.project_id == project_id, Membership.user_id == user_id)
        .first()
    )

    if not membership:
        return {
            "can_edit_metadata": False,
            "can_edit_paths": False,
            "can_create_release": False,
            "can_manage_rdmp": False,
        }

    # Get current RDMP
    rdmp = get_current_rdmp(db, project_id)
    if not rdmp:
        return {
            "can_edit_metadata": False,
            "can_edit_paths": False,
            "can_create_release": False,
            "can_manage_rdmp": False,
        }

    # Find role in RDMP
    rdmp_json = rdmp.rdmp_json
    role = next(
        (r for r in rdmp_json.get("roles", []) if r["name"] == membership.role_name),
        None
    )

    if not role:
        return {
            "can_edit_metadata": False,
            "can_edit_paths": False,
            "can_create_release": False,
            "can_manage_rdmp": False,
        }

    return role.get("permissions", {})


def check_permission(db: Session, user: User, project_id: int, permission_name: str) -> bool:
    """Check if user has specific permission for a project."""
    permissions = get_user_permissions(db, user.id, project_id)
    return permissions.get(permission_name, False)


def require_project_permission(permission_name: str):
    """Decorator to require specific project permission."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract project_id from kwargs or path params
            project_id = kwargs.get("project_id")
            if not project_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Project ID not provided"
                )

            # Extract current_user and db from dependencies
            current_user = kwargs.get("current_user")
            db = kwargs.get("db")

            if not current_user or not db:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Missing required dependencies"
                )

            # Check permission
            if not check_permission(db, current_user, project_id, permission_name):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions: {permission_name} required"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator
