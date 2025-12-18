"""Helpers for storing and serving profile images from Azure Blob Storage."""

from __future__ import annotations

import logging
import mimetypes
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4
from urllib.parse import urlparse

from azure.core.exceptions import AzureError, ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.storage.blob import (
    BlobServiceClient,
    ContentSettings,
    ContainerClient,
    ContainerSasPermissions,
    generate_container_sas as azure_generate_container_sas,
)


logger = logging.getLogger(__name__)


class StorageConfigurationError(RuntimeError):
    """Raised when mandatory blob storage configuration is missing."""


class ImageValidationError(ValueError):
    """Raised when an uploaded file does not meet image requirements."""


class ImageStorageError(RuntimeError):
    """Raised when the blob service cannot complete an operation."""


_SERVICE_CLIENT: Optional[BlobServiceClient] = None


def _get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise StorageConfigurationError(f"Environment variable {name} is not configured")
    return value


def _get_service_client() -> BlobServiceClient:
    global _SERVICE_CLIENT

    account_url = _get_required_env("STORAGE_URL").rstrip("/")
    if _SERVICE_CLIENT is None:
        credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)
        _SERVICE_CLIENT = BlobServiceClient(account_url=account_url, credential=credential)
    return _SERVICE_CLIENT


def _get_container_client() -> ContainerClient:
    container_name = _get_required_env("STORAGE_CONTAINER")
    return _get_service_client().get_container_client(container_name)


def _build_blob_url(blob_name: str) -> str:
    base_url = _get_required_env("STORAGE_URL").rstrip("/")
    container_name = _get_required_env("STORAGE_CONTAINER")
    return f"{base_url}/{container_name}/{blob_name}"


def _extract_blob_name(image_url: str | None) -> Optional[str]:
    if not image_url:
        return None

    try:
        parsed = urlparse(image_url)
    except ValueError:
        return None

    path = parsed.path.lstrip("/")
    container_name = os.getenv("STORAGE_CONTAINER")
    if not container_name:
        return None
    prefix = f"{container_name}/"
    if path.startswith(prefix):
        blob_path = path[len(prefix) :]
        return blob_path.split("?")[0]
    return None


def _extension_for(content_type: Optional[str], filename: Optional[str]) -> str:
    if content_type:
        guessed = mimetypes.guess_extension(content_type)
        if guessed:
            return ".jpeg" if guessed == ".jpe" else guessed
    if filename and "." in filename:
        return filename[filename.rfind(".") :]
    return ""


def _validate_image(content_type: Optional[str], size: int) -> None:
    if not content_type or not content_type.startswith("image/"):
        raise ImageValidationError("Only image uploads are supported")
    # Restrict uploads to a reasonable size (10 MB) to protect the service.
    if size > 10 * 1024 * 1024:
        raise ImageValidationError("Image files must be 10 MB or smaller")


def store_profile_image(file) -> Optional[str]:
    """Upload ``file`` to blob storage and return the public URL without SAS."""

    if file is None:
        return None

    content_type = getattr(file, "content_type", None)
    filename = getattr(file, "filename", None)
    buffer = getattr(file, "file", None)

    if buffer is None:
        raise ImageValidationError("Invalid upload payload")

    position = buffer.tell()
    buffer.seek(0)
    data = buffer.read()
    buffer.seek(position)

    if not data:
        raise ImageValidationError("Uploaded file was empty")

    _validate_image(content_type, len(data))

    extension = _extension_for(content_type, filename)
    blob_name = f"profiles/{uuid4().hex}{extension}"

    try:
        container_client = _get_container_client()
        container_client.upload_blob(
            blob_name,
            data,
            overwrite=True,
            content_settings=ContentSettings(content_type=content_type),
        )
    except AzureError as exc:  # pragma: no cover - depends on Azure runtime
        logger.exception("Failed to upload profile image: %s", exc)
        raise ImageStorageError("Unable to upload profile image") from exc

    return _build_blob_url(blob_name)


def delete_profile_image(image_url: Optional[str]) -> None:
    """Remove ``image_url`` from blob storage if it exists."""

    blob_name = _extract_blob_name(image_url)
    if not blob_name:
        return
    try:
        container_client = _get_container_client()
    except StorageConfigurationError:
        # Deletion is best-effort; lack of configuration should not fail the request.
        logger.debug("Storage configuration missing; skipping deletion for %s", blob_name)
        return
    try:
        blob_client = container_client.get_blob_client(blob_name)
        blob_client.delete_blob(delete_snapshots="include")
    except ResourceNotFoundError:
        logger.debug("Blob %s already removed", blob_name)
    except AzureError as exc:  # pragma: no cover - depends on Azure runtime
        logger.warning("Failed to delete blob %s: %s", blob_name, exc)


def create_profile_container_sas(hours: int = 24) -> tuple[str, datetime]:
    """Return a SAS token permitting read access to the profile container."""

    if hours <= 0:
        raise ValueError("SAS duration must be positive")

    service_client = _get_service_client()
    container_client = service_client.get_container_client(_get_required_env("STORAGE_CONTAINER"))
    start = datetime.now(timezone.utc) - timedelta(minutes=5)
    expiry = start + timedelta(hours=hours)

    try:
        delegation_key = service_client.get_user_delegation_key(start, expiry)
    except AzureError as exc:  # pragma: no cover - depends on Azure runtime
        logger.exception("Failed to obtain user delegation key: %s", exc)
        raise ImageStorageError("Unable to generate SAS token") from exc

    try:
        token = azure_generate_container_sas(
            account_name=service_client.account_name,
            container_name=container_client.container_name,
            user_delegation_key=delegation_key,
            permission=ContainerSasPermissions(read=True, list=True),
            expiry=expiry,
        )
    except AzureError as exc:  # pragma: no cover - depends on Azure runtime
        logger.exception("Failed to generate SAS token: %s", exc)
        raise ImageStorageError("Unable to generate SAS token") from exc

    return token, expiry

