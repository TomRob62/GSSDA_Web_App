"""
Pydantic models for request and response schemas.

These schemas represent the API contracts exposed by the FastAPI
application. They validate incoming payloads and shape outgoing JSON
data. Where appropriate, nested models are used to fully describe
relationships (e.g. ``Room`` includes a list of ``RoomDescription``).

All timestamps are handled as aware ``datetime`` objects; FastAPI
serializes them to ISO 8601 strings with timezone offsets.
"""

from __future__ import annotations

import datetime
from typing import List, Optional, Union

from pydantic import BaseModel, Field, field_validator, ValidationInfo, model_validator

### Authentication Schemas ###


class Token(BaseModel):
    """Response schema for successful login."""

    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    """Payload for login requests."""

    username: str
    password: str


### User Schemas ###


class UserOut(BaseModel):
    """Public representation of a user."""

    id: int
    username: str
    role: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


### Room and RoomDescription Schemas ###


class RoomDescriptionBase(BaseModel):
    """Shared fields for room description payloads."""

    description: Optional[str] = None
    start_time: Optional[datetime.datetime] = None
    end_time: Optional[datetime.datetime] = None

    @field_validator("end_time", mode="after")
    def check_end_after_start(cls, end_time, info: ValidationInfo):
        start_time = info.data.get("start_time")
        if end_time and start_time and end_time <= start_time:
            raise ValueError("End time must be after start time")
        return end_time


class RoomDescriptionCreate(RoomDescriptionBase):
    """Schema for creating a room description."""

    description: Optional[str] = None


class RoomDescriptionUpdate(RoomDescriptionBase):
    """Schema for updating an existing room description."""

    id: Optional[int] = None


class RoomDescriptionOut(RoomDescriptionBase):
    """Response schema for room descriptions."""

    id: int

    model_config = {"from_attributes": True}


class RoomBase(BaseModel):
    """Fields common to room create/update payloads."""

    room_number: str
    static: bool


class RoomCreate(RoomBase):
    """Schema for creating rooms including descriptions."""

    descriptions: List[RoomDescriptionCreate]

    @field_validator("descriptions", mode="after")
    def check_descriptions(cls, v, info: ValidationInfo):
        static = info.data.get("static")
        if static:
            # Only allow one timeless description if static
            if len(v) != 1:
                raise ValueError("Static rooms must have exactly one description")
            desc = v[0]
            if desc.start_time or desc.end_time:
                raise ValueError(
                    "Static rooms must not have start_time or end_time on the description"
                )
        else:
            # Non-static: require at least one time-bound description
            if not v:
                raise ValueError(
                    "Non-static rooms must include at least one time-bound description"
                )
            # Ensure no overlapping time ranges
            sorted_desc = sorted(v, key=lambda d: d.start_time or datetime.datetime.min)
            for i in range(len(sorted_desc) - 1):
                current = sorted_desc[i]
                nxt = sorted_desc[i + 1]
                if current.end_time and nxt.start_time and current.end_time > nxt.start_time:
                    raise ValueError("Room descriptions may not overlap in time")
        return v


class RoomUpdate(RoomBase):
    """Schema for partial room updates."""

    id: Optional[int] = None
    room_number: Optional[str] = None
    static: Optional[bool] = None
    descriptions: Optional[List[RoomDescriptionUpdate]] = None


class RoomOut(RoomBase):
    """Response schema representing a persisted room."""

    id: int
    descriptions: List[RoomDescriptionOut]
    created_at: datetime.datetime
    updated_at: datetime.datetime
    version: int

    model_config = {"from_attributes": True}


### CallerCuer Schemas ###


class CallerCuerBase(BaseModel):
    """Shared fields for caller/cuer operations."""

    first_name: str
    last_name: str
    suffix: Optional[str] = None
    mc: bool = False
    dance_types: Optional[List[str]] = Field(default_factory=list)

    @field_validator("dance_types")
    def normalize_dance_type(cls, value):
        # Accept None or list; ensure no empty strings in the list
        if value is None:
            return value
        # If a single string was provided, coerce to list
        if isinstance(value, str):
            value = [value]
        cleaned = []
        for item in value:
            if not item:
                raise ValueError("Dance type cannot be empty")
            cleaned.append(item)
        return cleaned


class CallerCuerCreate(CallerCuerBase):
    """Schema for creating caller/cuer records."""

    pass


class CallerCuerUpdate(BaseModel):
    """Schema for updating caller/cuer records."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    suffix: Optional[str] = None
    mc: Optional[bool] = None
    dance_types: Optional[List[str]] = None


class CallerCuerOut(CallerCuerBase):
    """Response schema for caller/cuer records."""

    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    version: int

    model_config = {"from_attributes": True}


### Event Schemas ###


class EventBase(BaseModel):
    """Shared fields for event create/update operations."""

    room_id: int
    caller_cuer_ids: List[int] = Field(default_factory=list)
    start: datetime.datetime
    end: datetime.datetime
    dance_types: Optional[List[str]] = Field(default_factory=list)
    @field_validator("end", mode="after")
    def check_end_after_start(cls, end, info: ValidationInfo):
        start = info.data.get("start")
        if end <= start:
            raise ValueError("End time must be after start time")
        return end


class EventCreate(EventBase):
    """Schema for creating events."""

    @field_validator("caller_cuer_ids")
    def check_callers(cls, caller_ids):
        cleaned = [cid for cid in caller_ids if cid is not None]
        if not cleaned:
            raise ValueError("At least one caller/cuer must be assigned")
        if len(set(cleaned)) != len(cleaned):
            raise ValueError("Caller/Cuer selections must be unique")
        return cleaned


class EventUpdate(BaseModel):
    """Schema for updating events."""

    room_id: Optional[int] = None
    caller_cuer_ids: Optional[List[int]] = None
    start: Optional[datetime.datetime] = None
    end: Optional[datetime.datetime] = None
    dance_types: Optional[List[str]] = None

    @field_validator("caller_cuer_ids")
    def validate_caller_list(cls, caller_ids):
        if caller_ids is None:
            return None
        cleaned = [cid for cid in caller_ids if cid is not None]
        if not cleaned:
            raise ValueError("Caller/Cuer list cannot be empty")
        if len(set(cleaned)) != len(cleaned):
            raise ValueError("Caller/Cuer selections must be unique")
        return cleaned


class EventOut(EventBase):
    """Response schema for persisted events."""

    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    version: int

    model_config = {"from_attributes": True}


class DayFilterOption(BaseModel):
    """Metadata describing a selectable day filter option."""

    value: str
    label: str
    count: int
    day_key: str
    first_start: Optional[str] = None


### MC Schemas ###


class MCBase(BaseModel):
    """Shared fields for MC scheduling."""

    room_id: int
    caller_cuer_id: int
    start: datetime.datetime
    end: datetime.datetime

    @field_validator("end", mode="after")
    def check_end_after_start(cls, end, info: ValidationInfo):
        start = info.data.get("start")
        if end <= start:
            raise ValueError("End time must be after start time")
        return end


class MCCreate(MCBase):
    """Schema for creating MC assignments."""

    pass


class MCUpdate(BaseModel):
    """Schema for updating MC assignments."""

    room_id: Optional[int] = None
    caller_cuer_id: Optional[int] = None
    start: Optional[datetime.datetime] = None
    end: Optional[datetime.datetime] = None


class MCOut(MCBase):
    """Response schema for MC assignments."""

    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    version: int
    model_config = {"from_attributes": True}


### Profile Schemas ###


class ProfileBase(BaseModel):
    """Fields shared across profile create/update operations."""

    caller_cuer_id: Optional[int] = None
    advertisement: bool = False
    image_path: Optional[str] = None
    content: Optional[str] = None

    @model_validator(mode="after")
    def _check_caller_requirement(self) -> "ProfileBase":
        if not self.advertisement and self.caller_cuer_id is None:
            raise ValueError("caller_cuer_id is required unless advertisement is true")
        return self


class ProfileCreate(ProfileBase):
    """Schema for creating a caller profile."""

    pass


class ProfileUpdate(BaseModel):
    """Schema for updating existing profiles."""

    caller_cuer_id: Optional[int] = None
    image_path: Optional[str] = None
    content: Optional[str] = None
    advertisement: Optional[bool] = None


class ProfileCaller(BaseModel):
    """Denormalised caller summary bundled with a profile."""

    id: int
    first_name: str
    last_name: str
    suffix: Optional[str] = None

    model_config = {"from_attributes": True}


class ProfileOut(ProfileBase):
    """Response schema for caller profiles."""

    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    version: int
    caller: Optional[ProfileCaller] = None

    model_config = {"from_attributes": True}


### Generic Response Schemas ###


class PaginatedResponse(BaseModel):
    """Generic envelope for paginated list responses."""

    data: List[Union[RoomOut, CallerCuerOut, EventOut, MCOut, ProfileOut]]
    page: int
    page_size: int
    total: int
    next_cursor: Optional[str] = None


class SasTokenResponse(BaseModel):
    """Envelope for SAS token responses."""

    token: str
    expires_at: datetime.datetime
