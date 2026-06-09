from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Security
from fastapi.security import APIKeyHeader
from starlette.exceptions import HTTPException
from starlette.status import HTTP_401_UNAUTHORIZED

from src.config import Settings, load_settings

API_KEY_HEADER = APIKeyHeader(
    name="X-API-Key",
    scheme_name="X-API-Key",
    description="API key required to run the newsletter pipeline.",
    auto_error=True,
)


@lru_cache
def get_settings() -> Settings:
    return load_settings()


async def validate_api_key(
    api_key: Annotated[str, Security(API_KEY_HEADER)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> str:
    if api_key != settings.fastapi_api_key.get_secret_value():
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )
    return api_key
