"""Controller utilities for caller profiles."""

from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, UploadFile, status

from DAL import schemas
from Services import profiles as profile_service
from Services import profile_images


def _upload_image(upload: UploadFile | None) -> str | None:
    if upload is None:
        return None
    try:
        return profile_images.store_profile_image(upload)
    except profile_images.ImageValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except profile_images.StorageConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    except profile_images.ImageStorageError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


def _convert_profile(profile: dict) -> schemas.ProfileOut:
    """Map a service-layer dict into a Pydantic schema."""

    caller_data = profile.get("caller") or None
    caller_schema = None
    if caller_data and caller_data.get("id") is not None:
        caller_schema = schemas.ProfileCaller(
            id=caller_data.get("id", profile.get("caller_cuer_id")),
            first_name=caller_data.get("first_name", ""),
            last_name=caller_data.get("last_name", ""),
            suffix=caller_data.get("suffix"),
        )
    return schemas.ProfileOut(
        id=profile["id"],
        caller_cuer_id=profile["caller_cuer_id"],
        image_path=profile.get("image_path"),
        content=profile.get("content"),
        created_at=profile["created_at"],
        updated_at=profile["updated_at"],
        version=profile.get("version", 1),
        advertisement=bool(profile.get("advertisement", False)),
        caller=caller_schema,
    )


def create_profile_controller(data: schemas.ProfileCreate) -> schemas.ProfileOut:
    """Create a new profile and serialise the response."""

    profile = profile_service.create_profile(data)
    return _convert_profile(profile)


def create_profile_from_form_controller(
    *,
    caller_cuer_id: int | None,
    content: str | None,
    image: UploadFile | None,
    advertisement: bool = False,
) -> schemas.ProfileOut:
    """Create a profile from multipart form inputs."""

    image_url = _upload_image(image)
    payload = schemas.ProfileCreate(
        caller_cuer_id=caller_cuer_id,
        content=content,
        image_path=image_url,
        advertisement=advertisement,
    )
    return create_profile_controller(payload)


def list_profiles_controller(
    *,
    q: str | None = None,
    sort: str | None = None,
    page: int = 1,
    page_size: int = 50,
    caller_cuer_id: int | None = None,
    has_image: bool | None = None,
    has_content: bool | None = None,
    advertisement: bool | None = None,
) -> schemas.PaginatedResponse:
    """Return a paginated collection of profiles."""

    profiles, total = profile_service.list_profiles(
        q=q,
        sort=sort,
        page=page,
        page_size=page_size,
        caller_cuer_id=caller_cuer_id,
        has_image=has_image,
        has_content=has_content,
        advertisement=advertisement,
    )
    data = [_convert_profile(item) for item in profiles]
    return schemas.PaginatedResponse(data=data, page=page, page_size=page_size, total=total)


def get_profile_controller(profile_id: int) -> schemas.ProfileOut:
    """Retrieve a profile by identifier."""

    profile = profile_service.get_profile(profile_id)
    return _convert_profile(profile)


def get_profile_by_caller_controller(caller_id: int) -> Optional[schemas.ProfileOut]:
    """Return a profile for ``caller_id`` if it exists."""

    try:
        profile = profile_service.get_profile_by_caller(caller_id)
    except HTTPException as exc:  # pragma: no cover - defensive re-mapping
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            return None
        raise
    return _convert_profile(profile)


def update_profile_controller(profile_id: int, data: schemas.ProfileUpdate) -> schemas.ProfileOut:
    """Update profile attributes and return the persisted representation."""

    profile = profile_service.update_profile(profile_id, data)
    return _convert_profile(profile)


def update_profile_from_form_controller(
    profile_id: int,
    *,
    caller_cuer_id: int | None,
    content: str | None,
    image: UploadFile | None,
    remove_image: bool = False,
    advertisement: bool | None = None,
) -> schemas.ProfileOut:
    """Update a profile using multipart form inputs."""

    current = profile_service.get_profile(profile_id)
    image_url = current.get("image_path")

    update_kwargs: dict[str, object] = {}
    if caller_cuer_id is not None:
        update_kwargs["caller_cuer_id"] = caller_cuer_id
    if content is not None:
        update_kwargs["content"] = content
    if advertisement is not None:
        update_kwargs["advertisement"] = advertisement

    if remove_image:
        profile_images.delete_profile_image(image_url)
        update_kwargs["image_path"] = None
        image_url = None
    elif image is not None:
        new_url = _upload_image(image)
        if new_url:
            update_kwargs["image_path"] = new_url
            profile_images.delete_profile_image(image_url)
            image_url = new_url

    if not update_kwargs:
        update_kwargs["caller_cuer_id"] = current["caller_cuer_id"]

    payload = schemas.ProfileUpdate(**update_kwargs)
    return update_profile_controller(profile_id, payload)


def list_advertisement_profiles_controller(limit: int | None = None) -> list[schemas.ProfileOut]:
    """Return advertisement profiles for presentation displays."""

    profiles = profile_service.list_advertisement_profiles(limit=limit)
    return [_convert_profile(profile) for profile in profiles]


def delete_profile_controller(profile_id: int) -> None:
    """Delete a profile."""

    profile = profile_service.get_profile(profile_id)
    profile_images.delete_profile_image(profile.get("image_path"))
    profile_service.delete_profile(profile_id)


def generate_profile_image_sas_controller(hours: int = 24) -> schemas.SasTokenResponse:
    """Return a SAS token for profile image access."""

    try:
        token, expiry = profile_images.create_profile_container_sas(hours=hours)
    except profile_images.StorageConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    except profile_images.ImageStorageError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return schemas.SasTokenResponse(token=token, expires_at=expiry)


# Re-export converter for advanced search integration
convert_profile = _convert_profile
