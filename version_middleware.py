import re
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Optional
from version_config import version_manager, VersionStatus


class VersionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.version_pattern = re.compile(r'^/v(\d+)(/.*)?$')

    async def dispatch(self, request: Request, call_next):
        request.state.api_version = self._extract_version(request)
        request.state.path_without_version = self._strip_version_prefix(request.url.path)
        request.scope["path"] = request.state.path_without_version

        response = await call_next(request)

        version_config = version_manager.get_version(request.state.api_version)
        if version_config.status == VersionStatus.DEPRECATED:
            response.headers["X-Deprecated"] = "true"
            if version_config.sunset_date:
                response.headers["X-Sunset-Date"] = version_config.sunset_date
        response.headers["X-API-Version"] = str(version_config.version)

        return response

    def _extract_version(self, request: Request) -> Optional[int]:
        path = request.url.path
        match = self.version_pattern.match(path)
        if match:
            return int(match.group(1))

        version_header = request.headers.get("X-API-Version")
        if version_header:
            try:
                return int(version_header)
            except ValueError:
                pass

        return None

    def _strip_version_prefix(self, path: str) -> str:
        match = self.version_pattern.match(path)
        if match:
            remaining = match.group(2) or "/"
            return remaining
        return path
