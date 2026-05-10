from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from app.version_config import (
    get_version_def,
    LATEST_VERSION,
    SUPPORTED_VERSIONS,
    transform_response,
)
import re


class VersionMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        original_path = request.url.path
        version = self._resolve_version_from_header(request)
        path_version = self._extract_version_from_path(original_path)

        if path_version is not None:
            version = path_version
            stripped = re.sub(r"^/v\d+", "", original_path)
            if not stripped:
                stripped = "/"
            request.scope["path"] = stripped
            request.scope["raw_path"] = stripped.encode()

        request.state.api_version = version

        response = await call_next(request)

        version_def = get_version_def(version)
        if version_def and version_def.is_deprecated:
            response.headers["X-Deprecated"] = "true"
            if version_def.sunset_date:
                response.headers["X-Sunset-Date"] = version_def.sunset_date

        response.headers["X-API-Version"] = str(version)
        return response

    def _resolve_version_from_header(self, request: Request) -> int:
        header_version = request.headers.get("X-API-Version")
        if header_version:
            try:
                v = int(header_version)
                if v in SUPPORTED_VERSIONS:
                    return v
            except ValueError:
                pass
        return LATEST_VERSION

    def _extract_version_from_path(self, path: str) -> int | None:
        match = re.match(r"^/v(\d+)/", path)
        if match:
            try:
                v = int(match.group(1))
                if v in SUPPORTED_VERSIONS:
                    return v
            except ValueError:
                pass
        return None
