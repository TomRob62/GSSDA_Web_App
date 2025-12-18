"""
Database models for the Event Organizer application.

These SQLAlchemy models represent the core entities described in the
Software Design Documents (SDD). Each model includes relationships
consistent with the data model section, along with columns for basic
metadata such as ``created_at``, ``updated_at`` and an optimistic
concurrency control ``version`` field. Time stamps are stored in UTC
using ISO 8601 and can be converted on the client side to local time.

Relationships:

* ``Room`` has many ``RoomDescription``, ``Event``, and ``MC`` records.
* ``CallerCuer`` has many ``Event`` and ``MC`` records.
* ``Event`` references exactly one ``Room`` and one or more ``CallerCuer``
  records via the ``event_callers`` junction table.
* ``MC`` references exactly one ``Room`` and one ``CallerCuer``.

The ``User`` model supports authentication with a hashed password and
assigned role.
"""

from __future__ import annotations

import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from .db import Base


event_callers_table = Table(
    "event_callers",
    Base.metadata,
    Column("event_id", ForeignKey("events.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "caller_cuer_id",
        ForeignKey("caller_cuers.id", ondelete="RESTRICT"),
        primary_key=True,
    ),
    Column("position", Integer, nullable=False, default=0),
)


class User(Base):
    """Represents an authenticated user.

    Passwords are stored
    using a secure hash algorithm (bcrypt) via passlib in the service
    layer. Roles determine access control; the default role for the
    built-in user is ``admin``.
    """

    __tablename__ = "users"

    id: int = Column(Integer, primary_key=True, index=True)
    username: str = Column(String(50), unique=True, nullable=False)
    hashed_password: str = Column(String(128), nullable=False)
    role: str = Column(String(20), default="admin", nullable=False)
    created_at: datetime.datetime = Column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    updated_at: datetime.datetime = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )
    version: int = Column(Integer, default=1, nullable=False)

    # No relationships defined here; users currently do not own any records.


class Room(Base):
    """Represents a physical room where events and MC sessions occur."""

    __tablename__ = "rooms"

    id: int = Column(Integer, primary_key=True, index=True)
    room_number: str = Column(String(100), unique=False, nullable=False)
    static: bool = Column(Boolean, nullable=False, default=True)
    created_at: datetime.datetime = Column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    updated_at: datetime.datetime = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )
    version: int = Column(Integer, default=1, nullable=False)

    # Relationships
    descriptions: List["RoomDescription"] = relationship(
        "RoomDescription",
        back_populates="room",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    events: List["Event"] = relationship(
        "Event",
        back_populates="room",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    mcs: List["MC"] = relationship(
        "MC",
        back_populates="room",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class RoomDescription(Base):
    """Time-bound or timeless description of a room."""

    __tablename__ = "room_descriptions"

    id: int = Column(Integer, primary_key=True, index=True)
    room_id: int = Column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    start_time: Optional[datetime.datetime] = Column(DateTime(timezone=True), nullable=True)
    end_time: Optional[datetime.datetime] = Column(DateTime(timezone=True), nullable=True)
    description: str = Column(Text, nullable=True)

    created_at: datetime.datetime = Column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    updated_at: datetime.datetime = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )
    version: int = Column(Integer, default=1, nullable=False)

    # Relationship back to room
    room: "Room" = relationship("Room", back_populates="descriptions")


class CallerCuer(Base):
    """Represents a caller or cuer."""

    __tablename__ = "caller_cuers"

    id: int = Column(Integer, primary_key=True, index=True)
    first_name: str = Column(String(100), nullable=False)
    last_name: str = Column(String(100), nullable=False)
    suffix: Optional[str] = Column(String(50), nullable=True)
    mc: bool = Column(Boolean, nullable=False, default=False)
    dance_types: Optional[str] = Column(Text, nullable=True)
    created_at: datetime.datetime = Column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    updated_at: datetime.datetime = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )
    version: int = Column(Integer, default=1, nullable=False)

    # Relationships
    events: List["Event"] = relationship(
        "Event",
        secondary=event_callers_table,
        back_populates="callers",
        lazy="selectin",
    )
    mcs: List["MC"] = relationship(
        "MC",
        back_populates="caller_cuer",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    profile: Optional["Profile"] = relationship(
        "Profile",
        back_populates="caller",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class Profile(Base):
    """Narrative and imagery for a caller/cuer."""

    __tablename__ = "profiles"

    id: int = Column(Integer, primary_key=True, index=True)
    caller_cuer_id: Optional[int] = Column(
        Integer,
        ForeignKey("caller_cuers.id", ondelete="CASCADE"),
        nullable=True,
    )
    advertisement: bool = Column(Boolean, nullable=False, default=False)
    image_path: Optional[str] = Column(Text, nullable=True)
    content: Optional[str] = Column(Text, nullable=True)
    created_at: datetime.datetime = Column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    updated_at: datetime.datetime = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )
    version: int = Column(Integer, default=1, nullable=False)

    caller: Optional["CallerCuer"] = relationship("CallerCuer", back_populates="profile")


class Event(Base):
    """Scheduled session performed by one or more callers/cuers in a room."""

    __tablename__ = "events"

    id: int = Column(Integer, primary_key=True, index=True)
    room_id: int = Column(Integer, ForeignKey("rooms.id", ondelete="RESTRICT"), nullable=False)
    start: datetime.datetime = Column(DateTime(timezone=True), nullable=False)
    end: datetime.datetime = Column(DateTime(timezone=True), nullable=False)
    dance_types: Optional[str] = Column(Text, nullable=True)
    created_at: datetime.datetime = Column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    updated_at: datetime.datetime = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )
    version: int = Column(Integer, default=1, nullable=False)

    # Relationships
    room: "Room" = relationship("Room", back_populates="events")
    callers: List["CallerCuer"] = relationship(
        "CallerCuer",
        secondary=event_callers_table,
        back_populates="events",
        order_by=event_callers_table.c.position,
        lazy="selectin",
    )


class MC(Base):
    """Master of ceremonies assignment within a room."""

    __tablename__ = "mcs"

    id: int = Column(Integer, primary_key=True, index=True)
    room_id: int = Column(Integer, ForeignKey("rooms.id", ondelete="RESTRICT"), nullable=False)
    caller_cuer_id: int = Column(
        Integer, ForeignKey("caller_cuers.id", ondelete="RESTRICT"), nullable=False
    )
    start: datetime.datetime = Column(DateTime(timezone=True), nullable=False)
    end: datetime.datetime = Column(DateTime(timezone=True), nullable=False)
    created_at: datetime.datetime = Column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    updated_at: datetime.datetime = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )
    version: int = Column(Integer, default=1, nullable=False)

    # Relationships
    room: "Room" = relationship("Room", back_populates="mcs")
    caller_cuer: "CallerCuer" = relationship("CallerCuer", back_populates="mcs")
