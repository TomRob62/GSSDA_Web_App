"""Background worker responsible for pruning expired auth tokens."""

from __future__ import annotations

import asyncio
import logging
from contextlib import suppress
from typing import Optional

from fastapi import FastAPI

from Services import token_store

logger = logging.getLogger(__name__)

_CLEANUP_INTERVAL_SECONDS = 5 * 60  # 5 minutes
_TASK_ATTR = "token_cleanup_task"


async def _cleanup_loop() -> None:
    """Run until cancelled, purging expired tokens at regular intervals."""

    try:
        while True:
            removed = token_store.purge_expired_tokens()
            if removed:
                logger.info("Purged %s expired auth token(s)", removed)
            await asyncio.sleep(_CLEANUP_INTERVAL_SECONDS)
    except asyncio.CancelledError:  # pragma: no cover - graceful shutdown
        logger.debug("Token cleanup worker cancelled")
        raise


def start_worker(app: FastAPI) -> None:
    """Start the cleanup worker for ``app`` if not already running."""

    if getattr(app.state, _TASK_ATTR, None) is not None:
        return

    # Perform an eager cleanup at startup to avoid stale tokens.
    removed = token_store.purge_expired_tokens()
    if removed:
        logger.info("Purged %s expired auth token(s) during startup", removed)

    task = asyncio.create_task(_cleanup_loop())
    app.state.token_cleanup_task = task


async def stop_worker(app: FastAPI) -> None:
    """Stop the cleanup worker if it is running."""

    task: Optional[asyncio.Task] = getattr(app.state, _TASK_ATTR, None)
    if task is None:
        return

    task.cancel()
    with suppress(asyncio.CancelledError):
        await task
    setattr(app.state, _TASK_ATTR, None)
