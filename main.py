from datetime import date
from typing import Annotated, Any

from fastapi import FastAPI, Query, Security
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.exceptions import HTTPException
from starlette.requests import Request

from src.api.dependencies import validate_api_key
from src.api.ui import home_page
from src.logging_setup import setup_logging
from src.process_service import run_newsletter_process

setup_logging()

app = FastAPI(
    title="rAIdio",
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    if exc.status_code == 401 and exc.detail == "Not authenticated":
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid or missing API key."},
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None),
    )


@app.get("/", include_in_schema=False)
async def index() -> HTMLResponse:
    return home_page()


@app.post("/run-process", include_in_schema=False)
async def run_process(
    _api_key: Annotated[str, Security(validate_api_key)],
    target_date: date = Query(  # noqa: B008
        default_factory=date.today,
    ),
) -> dict[str, Any]:
    outcome = await run_newsletter_process(target_date=target_date)
    return {
        "status": outcome.status,
        "target_date": outcome.target_date.isoformat(),
        "detail": outcome.detail,
    }
