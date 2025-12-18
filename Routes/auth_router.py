"""Authentication routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Body, status
from fastapi.security import HTTPAuthorizationCredentials

from DAL import schemas
from Services import auth as auth_service
from Controllers import auth_controller


router = APIRouter()


@router.post("/login", response_model=schemas.Token)
async def login(credentials: schemas.LoginRequest = Body(...)):
    """Authenticate user and return an access token."""
    return await auth_controller.login_controller(credentials)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(auth_service.bearer_scheme),
):
    """Invalidate the current token."""

    token = auth_service.get_token_from_credentials(credentials)
    auth_controller.logout_controller(token)
    return None


@router.get("/session", response_model=schemas.UserOut)
async def check_session(user=Depends(auth_service.get_current_user)):
    """Return details about the current authenticated user."""

    return auth_controller.session_controller(user)
