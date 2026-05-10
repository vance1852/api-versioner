from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class VersionConfig:
    version: str
    status: str
    sunset_date: Optional[str] = None
    fields: List[str] = field(default_factory=list)
    field_transforms: Dict[str, Callable[[Dict[str, Any]], Any]] = field(default_factory=dict)
    field_renames: Dict[str, str] = field(default_factory=dict)
    changelog: str = ""


def _v1_full_name(data: Dict[str, Any]) -> str:
    return f"{data.get('first_name', '')} {data.get('last_name', '')}".strip()


def _v3_display_name(data: Dict[str, Any]) -> str:
    if data.get("display_name"):
        return data["display_name"]
    return data.get("full_name") or f"{data.get('first_name', '')} {data.get('last_name', '')}".strip()


VERSIONS: Dict[str, VersionConfig] = {
    "1": VersionConfig(
        version="1",
        status="deprecated",
        sunset_date="2025-12-31",
        fields=["id", "full_name", "email", "created_at"],
        field_transforms={"full_name": _v1_full_name},
        field_renames={},
        changelog="Initial version. User object contains 'full_name' field.",
    ),
    "2": VersionConfig(
        version="2",
        status="deprecated",
        sunset_date="2026-06-30",
        fields=["id", "first_name", "last_name", "email", "created_at"],
        field_transforms={},
        field_renames={},
        changelog="Split 'full_name' into 'first_name' and 'last_name'.",
    ),
    "3": VersionConfig(
        version="3",
        status="active",
        fields=["id", "first_name", "last_name", "display_name", "email", "created_at"],
        field_transforms={"display_name": _v3_display_name},
        field_renames={},
        changelog="Added 'display_name' field which is the preferred display name.",
    ),
}

LATEST_VERSION = "3"


def get_version_config(version: str) -> Optional[VersionConfig]:
    return VERSIONS.get(version)


def get_all_versions() -> List[Dict[str, Any]]:
    return [
        {
            "version": v.version,
            "status": v.status,
            "sunset_date": v.sunset_date,
            "changelog": v.changelog,
        }
        for v in VERSIONS.values()
    ]


def is_deprecated(version: str) -> bool:
    cfg = get_version_config(version)
    return cfg is not None and cfg.status == "deprecated"
