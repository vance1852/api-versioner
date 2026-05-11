from typing import Dict, List, Callable, Any, Optional
from enum import Enum


class VersionStatus(str, Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    SUNSET = "sunset"


class VersionConfig:
    def __init__(
        self,
        version: int,
        status: VersionStatus,
        sunset_date: Optional[str] = None,
        changelog: List[str] = None,
        fields: List[str] = None,
    ):
        self.version = version
        self.status = status
        self.sunset_date = sunset_date
        self.changelog = changelog or []
        self.fields = fields or []
        self.field_mappings: Dict[str, Dict[str, Callable]] = {}
        self.reverse_mappings: Dict[str, List[tuple]] = {}

    def add_field_mapping(
        self,
        old_field: str,
        new_field: str,
        to_new: Callable[[Any], Any],
        to_old: Optional[Callable[[Dict], Any]] = None,
    ):
        if old_field not in self.field_mappings:
            self.field_mappings[old_field] = {}
        self.field_mappings[old_field][new_field] = to_new

        if to_old is not None:
            if old_field not in self.reverse_mappings:
                self.reverse_mappings[old_field] = []
            self.reverse_mappings[old_field].append((new_field, to_old))


class VersionManager:
    def __init__(self):
        self.versions: Dict[int, VersionConfig] = {}
        self.latest_version: int = 0

    def add_version(self, config: VersionConfig):
        self.versions[config.version] = config
        if config.version > self.latest_version:
            self.latest_version = config.version

    def get_version(self, version: Optional[int]) -> VersionConfig:
        if version is None:
            return self.versions[self.latest_version]
        return self.versions.get(version, self.versions[self.latest_version])

    def get_all_versions(self) -> List[Dict]:
        return [
            {
                "version": v.version,
                "status": v.status.value,
                "sunset_date": v.sunset_date,
                "is_latest": v.version == self.latest_version,
            }
            for v in sorted(self.versions.values(), key=lambda x: x.version)
        ]

    def get_changelog(self, version: int) -> Optional[List[str]]:
        if version in self.versions:
            return self.versions[version].changelog
        return None

    def upgrade_data(self, data: Dict, from_version: int, to_version: int) -> Dict:
        if from_version >= to_version:
            return data.copy()

        result = data.copy()
        for v in range(from_version, to_version):
            config = self.versions.get(v + 1)
            if config:
                result = self._apply_upgrade(result, config)
        return result

    def _apply_upgrade(self, data: Dict, config: VersionConfig) -> Dict:
        result = data.copy()
        for old_field, mappings in config.field_mappings.items():
            if old_field in result:
                old_value = result.pop(old_field)
                for new_field, converter in mappings.items():
                    result[new_field] = converter(old_value)
        return result

    def downgrade_data(self, data: Dict, from_version: int, to_version: int) -> Dict:
        if from_version <= to_version:
            return data.copy()

        result = data.copy()
        for v in range(from_version, to_version, -1):
            config = self.versions.get(v)
            if config:
                result = self._apply_downgrade(result, config)

        target_config = self.versions.get(to_version)
        if target_config and target_config.fields:
            result = {k: v for k, v in result.items() if k in target_config.fields}

        return result

    def _apply_downgrade(self, data: Dict, config: VersionConfig) -> Dict:
        result = data.copy()
        for old_field, mappings in config.reverse_mappings.items():
            for new_field, converter in mappings:
                if new_field in result:
                    result[old_field] = converter(result)
                    break
        for old_field, mappings in config.reverse_mappings.items():
            for new_field, _ in mappings:
                if new_field in result:
                    result.pop(new_field, None)
        return result


def create_user_version_manager() -> VersionManager:
    vm = VersionManager()

    v1 = VersionConfig(
        version=1,
        status=VersionStatus.DEPRECATED,
        sunset_date="2025-12-31",
        changelog=[
            "Initial version with single full_name field",
            "User model: id, full_name",
        ],
        fields=["id", "full_name"],
    )
    vm.add_version(v1)

    v2 = VersionConfig(
        version=2,
        status=VersionStatus.DEPRECATED,
        sunset_date="2025-12-31",
        changelog=[
            "Split full_name into first_name and last_name",
            "User model: id, first_name, last_name",
            "Breaking change: full_name field removed",
        ],
        fields=["id", "first_name", "last_name"],
    )
    v2.add_field_mapping(
        old_field="full_name",
        new_field="first_name",
        to_new=lambda x: x.split(" ")[0] if " " in x else x,
        to_old=None,
    )
    v2.add_field_mapping(
        old_field="full_name",
        new_field="last_name",
        to_new=lambda x: x.split(" ")[1] if " " in x else "",
        to_old=lambda data: f"{data.get('first_name', '')} {data.get('last_name', '')}".strip(),
    )
    vm.add_version(v2)

    v3 = VersionConfig(
        version=3,
        status=VersionStatus.ACTIVE,
        changelog=[
            "Added display_name field for user preference",
            "User model: id, first_name, last_name, display_name",
            "display_name defaults to first_name + last_name",
        ],
        fields=["id", "first_name", "last_name", "display_name"],
    )
    vm.add_version(v3)

    return vm


version_manager = create_user_version_manager()
