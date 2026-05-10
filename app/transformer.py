from __future__ import annotations

from typing import Any, Dict, List

from .versions import VersionConfig, get_version_config


def transform_to_version(data: Dict[str, Any], target_version: str) -> Dict[str, Any]:
    cfg = get_version_config(target_version)
    if cfg is None:
        return data

    result: Dict[str, Any] = {}

    for field in cfg.fields:
        if field in cfg.field_transforms:
            result[field] = cfg.field_transforms[field](data)
        elif field in cfg.field_renames:
            result[field] = data.get(cfg.field_renames[field])
        else:
            result[field] = data.get(field)

    return result


def transform_list_to_version(items: List[Dict[str, Any]], target_version: str) -> List[Dict[str, Any]]:
    return [transform_to_version(item, target_version) for item in items]


def parse_body_for_version(body: Dict[str, Any], request_version: str) -> Dict[str, Any]:
    cfg = get_version_config(request_version)
    if cfg is None:
        return body

    result = dict(body)

    if request_version == "1":
        full_name = body.get("full_name", "")
        parts = full_name.split(" ", 1)
        result["first_name"] = parts[0]
        result["last_name"] = parts[1] if len(parts) > 1 else ""
        result.pop("full_name", None)
        if "display_name" not in result or not result["display_name"]:
            result["display_name"] = full_name
    elif request_version == "2":
        if "display_name" not in result or not result["display_name"]:
            result["display_name"] = f"{body.get('first_name', '')} {body.get('last_name', '')}".strip()

    return result
