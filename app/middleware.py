from __future__ import annotations

import re
from typing import Optional

from fastapi import Header, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .versions import LATEST_VERSION, VERSIONS, get_version_config, is_deprecated


URL_VERSION_PATTERN = re.compile(r"^/v(\d+)(/.*)?$")


def extract_version_from_url(path: str) -> Optional[str]:
    match = URL_VERSION_PATTERN.match(path)
    if match:
        version = match.group(1)
        if version in VERSIONS:
            return version
    return None


def get_request_version(request: Request) -> str:
    url_version = extract_version_from_url(request.url.path)
    if url_version:
        return url_version

    header_version = request.headers.get("x-api-version")
    if header_version and header_version in VERSIONS:
        return header_version

    return LATEST_VERSION


async def version_dependency(
    request: Request,
    x_api_version: Optional[str] = Header(None),
) -> str:
    return request.scope.get("api_version", LATEST_VERSION)


class VersionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        version = get_request_version(request)
        request.scope["api_version"] = version

        url_version = extract_version_from_url(request.url.path)
        if url_version:
            match = URL_VERSION_PATTERN.match(request.url.path)
            if match:
                rest = match.group(2) or "/"
                request.scope["path"] = rest

        response: Response = await call_next(request)

        if is_deprecated(version):
            cfg = get_version_config(version)
            response.headers["X-Deprecated"] = "true"
            if cfg and cfg.sunset_date:
                response.headers["X-Sunset-Date"] = cfg.sunset_date

        response.headers["X-API-Version"] = version

        return response
