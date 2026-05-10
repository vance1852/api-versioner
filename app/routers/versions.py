from fastapi import APIRouter
from app.version_config import VERSIONS, get_version_def

router = APIRouter(prefix="/api", tags=["versions"])


@router.get("/versions")
def list_versions():
    result = []
    for v in sorted(VERSIONS.keys()):
        vd = VERSIONS[v]
        entry = {
            "version": vd.version,
            "status": vd.status,
        }
        if vd.sunset_date:
            entry["sunset_date"] = vd.sunset_date
        result.append(entry)
    return result


@router.get("/versions/{version}/changelog")
def get_changelog(version: int):
    vd = get_version_def(version)
    if not vd:
        return {"error": "Version not found"}
    return {
        "version": vd.version,
        "status": vd.status,
        "changelog": vd.changelog,
    }
