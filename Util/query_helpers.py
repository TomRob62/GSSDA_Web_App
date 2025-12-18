"""Utility helpers for constructing dynamic SQL queries.

The service layer performs a significant amount of ad-hoc SQL string
building to express filtering, sorting, and pagination. Centralising the
common patterns keeps the service modules focused on domain logic while
ensuring consistent behaviour (for example, always using ``LIKE`` with
wildcards or gracefully handling invalid sort fields).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Mapping, MutableSequence, Optional, Sequence, Tuple


@dataclass
class QueryBuilder:
    """Accumulate ``WHERE`` conditions and positional parameters."""

    base_query: str
    _conditions: MutableSequence[str] = field(default_factory=list)
    params: MutableSequence[Any] = field(default_factory=list)

    def add_condition(self, condition: str, *values: Any) -> None:
        """Append ``condition`` (prefixed with ``AND``) if values are provided."""

        if not condition:
            return
        if values and any(value is None for value in values):
            return
        self._conditions.append(f" AND {condition}")
        self.params.extend(values)

    def add_raw_condition(self, condition: str) -> None:
        """Append ``condition`` without injecting any parameters."""

        if condition:
            self._conditions.append(f" AND {condition}")

    def build(self) -> Tuple[str, List[Any]]:
        """Return the final query and a list copy of the parameters."""

        return self.base_query + "".join(self._conditions), list(self.params)


def like_pattern(value: Optional[str]) -> Optional[str]:
    """Return a ``LIKE`` pattern (``%value%``) or ``None`` for falsey values."""

    if value:
        return f"%{value}%"
    return None


def build_order_clause(
    sort: Optional[str],
    *,
    allowed: Mapping[str, str],
    default: str,
) -> str:
    """Return an ``ORDER BY`` clause respecting allowed sort fields."""

    if not sort:
        return f" ORDER BY {default}"
    normalized = sort.replace("::", ":").replace(":", ",")
    field, *order_parts = [part.strip() for part in normalized.split(",") if part.strip()]
    column = allowed.get(field)
    if not column:
        return f" ORDER BY {default}"
    direction = order_parts[0].lower() if order_parts else "asc"
    return f" ORDER BY {column} {'DESC' if direction == 'desc' else 'ASC'}"


def apply_pagination(params: Sequence[Any], *, page: int, page_size: int) -> Tuple[List[Any], int]:
    """Extend ``params`` with pagination values and return the offset."""

    offset = max(page - 1, 0) * page_size
    extended = list(params) + [page_size, offset]
    return extended, offset
