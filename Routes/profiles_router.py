"""API routes for caller profiles."""

from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Path,
    Query,
    UploadFile,
    status,
)

from DAL import schemas
from Services import auth as auth_service
from Services import permissions
from Controllers import profiles_controller

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.post("", response_model=schemas.ProfileOut, status_code=status.HTTP_201_CREATED)
async def create_profile(
    caller_cuer_id: int | None = Form(None),
    content: str | None = Form(None),
    image_file: UploadFile | None = File(None),
    advertisement: bool = Form(False),
    user=Depends(permissions.require_write_access),
):
    """Create a profile for a caller."""

    return profiles_controller.create_profile_from_form_controller(
        caller_cuer_id=caller_cuer_id,
        content=content,
        image=image_file,
        advertisement=advertisement,
    )


@router.get("", response_model=schemas.PaginatedResponse)
async def list_profiles(
    user=Depends(auth_service.get_current_user),
    q: str | None = Query(None),
    sort: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    caller_cuer_id: int | None = Query(None),
    has_image: bool | None = Query(None),
    has_content: bool | None = Query(None),
    advertisement: bool | None = Query(None),
):
    """List profiles with optional filtering and pagination."""

    return profiles_controller.list_profiles_controller(
        q=q,
        sort=sort,
        page=page,
        page_size=page_size,
        caller_cuer_id=caller_cuer_id,
        has_image=has_image,
        has_content=has_content,
        advertisement=advertisement,
    )


@router.get("/{profile_id:int}", response_model=schemas.ProfileOut)
async def get_profile(
    profile_id: int = Path(..., ge=1),
    user=Depends(auth_service.get_current_user),
):
    """Retrieve a profile by its identifier."""

    return profiles_controller.get_profile_controller(profile_id)


@router.get("/by-caller/{caller_id:int}", response_model=schemas.ProfileOut)
async def get_profile_by_caller(
    caller_id: int = Path(..., ge=1),
    user=Depends(auth_service.get_current_user),
):
    """Fetch a profile for a caller if it exists."""

    profile = profiles_controller.get_profile_by_caller_controller(caller_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile


@router.patch("/{profile_id:int}", response_model=schemas.ProfileOut)
async def update_profile(
    profile_id: int = Path(..., ge=1),
    caller_cuer_id: int | None = Form(None),
    content: str | None = Form(None),
    remove_image: bool = Form(False),
    image_file: UploadFile | None = File(None),
    advertisement: bool | None = Form(None),
    user=Depends(permissions.require_write_access),
):
    """Update an existing profile."""

    return profiles_controller.update_profile_from_form_controller(
        profile_id,
        caller_cuer_id=caller_cuer_id,
        content=content,
        image=image_file,
        remove_image=remove_image,
        advertisement=advertisement,
    )


@router.delete("/{profile_id:int}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    profile_id: int = Path(..., ge=1),
    user=Depends(permissions.require_write_access),
):
    """Delete a profile."""

    profiles_controller.delete_profile_controller(profile_id)
    return None


@router.get("/image-sas", response_model=schemas.SasTokenResponse)
async def get_profile_image_sas(
    duration_hours: int = Query(24, ge=1, le=24),
    user=Depends(auth_service.get_current_user),
):
    """Return a SAS token for reading profile images."""

    return profiles_controller.generate_profile_image_sas_controller(hours=duration_hours)


@router.get("/advertisements", response_model=list[schemas.ProfileOut])
async def list_advertisement_profiles(
    limit: int | None = Query(None, ge=1, le=200),
    user=Depends(auth_service.get_current_user),
):
    """Return advertisement-ready profiles for presentation displays."""

    return profiles_controller.list_advertisement_profiles_controller(limit=limit)
