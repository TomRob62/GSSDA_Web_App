"""
Main entry point for the Event Organizer application.

This module initializes the FastAPI app, configures middleware (CORS
and logging), mounts static files for the frontend under ``/`` and
``/login`` routes, and includes API routers from the Routes package.
On startup it ensures the database schema is created and seeds the
master admin user if no users exist.

Run the application with ``uvicorn main:app``. When deployed to
Azure WebApp Service, ``main.py`` serves as the entry point.
"""

from __future__ import annotations

import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

from DAL.db import init_db
from Services import user_setup
from Services import token_cleanup

# Routers
from Routes import (
    rooms_router,
    caller_cuers_router,
    events_router,
    mcs_router,
    profiles_router,
    auth_router,
    advanced_router,
    export_router,
)

load_dotenv()  # Load environment variables from .env file

logger = logging.getLogger("event-organizer")
logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan tasks."""

    # Initialize schema
    init_db()

    # Seed master and attendee users
    user_setup.ensure_seed_users()

    token_cleanup.start_worker(app)

    try:
        yield
    finally:
        await token_cleanup.stop_worker(app)


app = FastAPI(
    title="Event Organizer",
    version="1.4",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Allow cross-origin requests from any origin for development; restrict in prod
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
public_dir = Path(__file__).resolve().parent / "Public"
if not public_dir.exists():
    # Create an empty Public directory if not present
    public_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(public_dir)), name="static")

# Templates directory for potential HTML rendering (unused in final)
templates = Jinja2Templates(directory=str(public_dir))


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"{request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Completed with status {response.status_code}")
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Return errors in a standardized envelope as per the SDD.

    The error code maps the status code into a descriptive string. Field
    errors are included when available.
    """
    code_map = {
        400: "VALIDATION_FAILED",
        401: "AUTHENTICATION_FAILED",
        403: "NOT_AUTHORIZED",
        404: "NOT_FOUND",
        409: "CONFLICT",
    }
    code = code_map.get(exc.status_code, "ERROR")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": code,
                "message": exc.detail,
            }
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
            }
        },
    )


@app.get("/")
async def serve_index() -> FileResponse:
    """Serve the default page.

    Prefer `login.html` as the application's default landing page. If
    `login.html` is not present, fall back to `index.html`. If neither is
    available, return a small JSON message for diagnostics.
    """
    # Prefer login as the default landing page
    login_file = public_dir / "login.html"
    if login_file.exists():
        return FileResponse(login_file)

    # Fall back to index.html if login isn't present
    index_file = public_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)

    return JSONResponse({"message": "Frontend not found"})


@app.get("/login")
async def serve_login() -> FileResponse:
    login_file = public_dir / "login.html"
    if login_file.exists():
        return FileResponse(login_file)
    return JSONResponse({"message": "Login page not found"})


@app.get("/presentation")
async def serve_presentation() -> FileResponse:
    presentation_file = public_dir / "presentation.html"
    if presentation_file.exists():
        return FileResponse(presentation_file)
    return JSONResponse({"message": "Presentation page not found"})


@app.get("/presentation/callers")
async def serve_caller_board() -> FileResponse:
    caller_board_file = public_dir / "caller-board.html"
    if caller_board_file.exists():
        return FileResponse(caller_board_file)
    return JSONResponse({"message": "Caller board not found"}, status_code=404)


# Include API routers under /api prefix
app.include_router(auth_router.router, prefix="/api")
app.include_router(rooms_router.router, prefix="/api", tags=["rooms"])
app.include_router(caller_cuers_router.router, prefix="/api", tags=["caller_cuers"])
app.include_router(events_router.router, prefix="/api", tags=["events"])
app.include_router(mcs_router.router, prefix="/api", tags=["mcs"])
app.include_router(profiles_router.router, prefix="/api", tags=["profiles"])
app.include_router(advanced_router.router, prefix="/api")
app.include_router(export_router.router, prefix="/api")
