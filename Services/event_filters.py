"""Service helpers that expose aggregate data for event filters."""

from __future__ import annotations

from typing import List

from DAL.db import get_db
from Util.date_filters import display_from_day_key, format_day_label
from Util.timezone_helpers import TimeZoneConverter, get_converter


def list_event_days(*, converter: TimeZoneConverter | None = None) -> List[dict]:
    """Return metadata for each unique day with scheduled events."""

    tz = get_converter(converter)
    with get_db() as db:
        rows = db.execute("SELECT start FROM events ORDER BY start").fetchall()

    accumulator: dict[str, dict[str, object]] = {}
    for row in rows:
        local_start = tz.as_user_timezone(row["start"])
        day_key = local_start.strftime("%m-%d")
        bucket = accumulator.setdefault(
            day_key, {"count": 0, "first_start": local_start}
        )
        bucket["count"] = int(bucket["count"]) + 1
        if local_start < bucket["first_start"]:
            bucket["first_start"] = local_start

    options: List[dict] = []
    for day_key, data in sorted(
        accumulator.items(), key=lambda item: item[1]["first_start"]
    ):
        count = int(data["count"])
        display_value = display_from_day_key(day_key)
        options.append(
            {
                "value": display_value,
                "label": format_day_label(day_key, count=count),
                "count": count,
                "day_key": day_key,
                "first_start": data["first_start"].isoformat(),
            }
        )

    return options
