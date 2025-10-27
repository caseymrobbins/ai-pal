"""
Plugin Dependency Management and Version Compatibility

Manages plugin dependencies and ensures version compatibility.
"""

import logging
import subprocess
import sys
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass
from packaging import version
from packaging.specifiers import SpecifierSet
from packaging.requirements import Requirement

from .base import PluginMetadata

logger = logging.getLogger(__name__)


@dataclass
class DependencyInfo:
    """Information about a dependency"""
    name: str
    specifier: str  # Version specifier (e.g., ">=1.0.0,<2.0.0")
    installed_version: Optional[str] = None
    is_satisfied: bool = False
    error: Optional[str] = None


class VersionChecker:
    """
    Checks version compatibility between plugins and the system.
    """

    SYSTEM_VERSION = "0.1.0"  # Current AI-PAL system version

    @staticmethod
    def is_compatible(
        plugin_min_version: str,
        plugin_max_version: Optional[str] = None,
        system_version: Optional[str] = None
    ) -> bool:
        """
        Check if plugin is compatible with system version.

        Args:
            plugin_min_version: Minimum required system version
            plugin_max_version: Maximum supported system version (optional)
            system_version: System version to check against (uses current if None)

        Returns:
            True if compatible, False otherwise
        """
        system_ver = version.parse(system_version or VersionChecker.SYSTEM_VERSION)
        min_ver = version.parse(plugin_min_version)

        # Check minimum version
        if system_ver < min_ver:
            logger.warning(
                f"System version {system_ver} is below plugin minimum {min_ver}"
            )
            return False

        # Check maximum version if specified
        if plugin_max_version:
            max_ver = version.parse(plugin_max_version)
            if system_ver > max_ver:
                logger.warning(
                    f"System version {system_ver} exceeds plugin maximum {max_ver}"
                )
                return False

        return True

    @staticmethod
    def check_plugin_metadata(metadata: PluginMetadata) -> Tuple[bool, Optional[str]]:
        """
        Check if plugin metadata indicates compatibility.

        Args:
            metadata: Plugin metadata

        Returns:
            Tuple of (is_compatible, error_message)
        """
        is_compatible = VersionChecker.is_compatible(
            metadata.min_system_version,
            metadata.max_system_version
        )

        if not is_compatible:
            error = (
                f"Plugin '{metadata.name}' requires system version "
                f">={metadata.min_system_version}"
            )
            if metadata.max_system_version:
                error += f" and <={metadata.max_system_version}"
            error += f", but current version is {VersionChecker.SYSTEM_VERSION}"

            return False, error

        return True, None

    @staticmethod
    def compare_versions(v1: str, v2: str) -> int:
        """
        Compare two version strings.

        Args:
            v1: First version
            v2: Second version

        Returns:
            -1 if v1 < v2, 0 if v1 == v2, 1 if v1 > v2
        """
        ver1 = version.parse(v1)
        ver2 = version.parse(v2)

        if ver1 < ver2:
            return -1
        elif ver1 > ver2:
            return 1
        else:
            return 0


class DependencyResolver:
    """
    Resolves and validates plugin dependencies.

    Checks if required Python packages are installed and satisfy version requirements.
    """

    def __init__(self):
        self._installed_packages: Dict[str, str] = {}
        self._refresh_installed_packages()

    def _refresh_installed_packages(self) -> None:
        """Refresh list of installed packages"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list", "--format=json"],
                capture_output=True,
                text=True,
                check=True,
            )

            import json
            packages = json.loads(result.stdout)

            self._installed_packages = {
                pkg["name"].lower(): pkg["version"]
                for pkg in packages
            }

            logger.debug(f"Detected {len(self._installed_packages)} installed packages")

        except Exception as e:
            logger.warning(f"Failed to refresh installed packages: {e}")
            self._installed_packages = {}

    def check_dependencies(
        self,
        metadata: PluginMetadata
    ) -> Tuple[bool, List[DependencyInfo]]:
        """
        Check if all plugin dependencies are satisfied.

        Args:
            metadata: Plugin metadata with dependencies

        Returns:
            Tuple of (all_satisfied, dependency_info_list)
        """
        if not metadata.dependencies:
            return True, []

        dep_info_list: List[DependencyInfo] = []
        all_satisfied = True

        for dep_string in metadata.dependencies:
            try:
                # Parse requirement (e.g., "requests>=2.28.0")
                req = Requirement(dep_string)
                dep_name = req.name.lower()

                # Check if package is installed
                installed_ver = self._installed_packages.get(dep_name)

                if installed_ver is None:
                    # Not installed
                    dep_info = DependencyInfo(
                        name=req.name,
                        specifier=str(req.specifier) if req.specifier else "*",
                        installed_version=None,
                        is_satisfied=False,
                        error=f"Package '{req.name}' is not installed",
                    )
                    all_satisfied = False

                else:
                    # Check version compatibility
                    is_satisfied = True
                    error = None

                    if req.specifier:
                        is_satisfied = version.parse(installed_ver) in req.specifier

                        if not is_satisfied:
                            error = (
                                f"Installed version {installed_ver} does not satisfy "
                                f"requirement {req.specifier}"
                            )
                            all_satisfied = False

                    dep_info = DependencyInfo(
                        name=req.name,
                        specifier=str(req.specifier) if req.specifier else "*",
                        installed_version=installed_ver,
                        is_satisfied=is_satisfied,
                        error=error,
                    )

                dep_info_list.append(dep_info)

            except Exception as e:
                logger.error(f"Error parsing dependency '{dep_string}': {e}")
                dep_info = DependencyInfo(
                    name=dep_string,
                    specifier="",
                    installed_version=None,
                    is_satisfied=False,
                    error=f"Invalid dependency format: {e}",
                )
                dep_info_list.append(dep_info)
                all_satisfied = False

        return all_satisfied, dep_info_list

    def install_dependencies(
        self,
        metadata: PluginMetadata,
        upgrade: bool = False
    ) -> Tuple[bool, List[str]]:
        """
        Install missing plugin dependencies.

        Args:
            metadata: Plugin metadata
            upgrade: If True, upgrade existing packages

        Returns:
            Tuple of (success, error_messages)
        """
        if not metadata.dependencies:
            return True, []

        errors = []

        for dep_string in metadata.dependencies:
            try:
                logger.info(f"Installing dependency: {dep_string}")

                cmd = [sys.executable, "-m", "pip", "install"]
                if upgrade:
                    cmd.append("--upgrade")
                cmd.append(dep_string)

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=False,
                )

                if result.returncode != 0:
                    error = f"Failed to install '{dep_string}': {result.stderr}"
                    logger.error(error)
                    errors.append(error)
                else:
                    logger.info(f"Successfully installed: {dep_string}")

            except Exception as e:
                error = f"Error installing '{dep_string}': {e}"
                logger.error(error)
                errors.append(error)

        # Refresh installed packages after installation
        if not errors:
            self._refresh_installed_packages()

        return len(errors) == 0, errors

    def get_dependency_tree(
        self,
        plugin_metadatas: List[PluginMetadata]
    ) -> Dict[str, List[str]]:
        """
        Build dependency tree for multiple plugins.

        Args:
            plugin_metadatas: List of plugin metadata

        Returns:
            Dictionary mapping plugin names to their dependency lists
        """
        tree = {}

        for metadata in plugin_metadatas:
            tree[metadata.name] = metadata.dependencies or []

        return tree

    def detect_conflicts(
        self,
        plugin_metadatas: List[PluginMetadata]
    ) -> List[Tuple[str, str, str]]:
        """
        Detect version conflicts between plugins.

        Args:
            plugin_metadatas: List of plugin metadata

        Returns:
            List of conflicts as (package_name, plugin1_req, plugin2_req)
        """
        conflicts = []

        # Group dependencies by package name
        dep_by_package: Dict[str, List[Tuple[str, str]]] = {}

        for metadata in plugin_metadatas:
            for dep_string in metadata.dependencies or []:
                try:
                    req = Requirement(dep_string)
                    pkg_name = req.name.lower()

                    if pkg_name not in dep_by_package:
                        dep_by_package[pkg_name] = []

                    dep_by_package[pkg_name].append((metadata.name, str(req.specifier)))

                except Exception as e:
                    logger.warning(f"Error parsing dependency '{dep_string}': {e}")

        # Check for conflicting version requirements
        for pkg_name, reqs in dep_by_package.items():
            if len(reqs) < 2:
                continue

            # Check if specifiers are compatible
            for i in range(len(reqs)):
                for j in range(i + 1, len(reqs)):
                    plugin1, spec1 = reqs[i]
                    plugin2, spec2 = reqs[j]

                    if not self._are_specifiers_compatible(spec1, spec2):
                        conflicts.append((pkg_name, f"{plugin1}:{spec1}", f"{plugin2}:{spec2}"))
                        logger.warning(
                            f"Dependency conflict detected: {pkg_name} "
                            f"({plugin1} requires {spec1}, {plugin2} requires {spec2})"
                        )

        return conflicts

    def _are_specifiers_compatible(self, spec1: str, spec2: str) -> bool:
        """Check if two version specifiers are compatible"""
        if not spec1 or not spec2:
            return True

        try:
            specifier1 = SpecifierSet(spec1)
            specifier2 = SpecifierSet(spec2)

            # Check if there's any version that satisfies both
            # This is a simplified check - in practice, we'd need to check actual available versions
            # For now, just check if the specifiers don't directly conflict
            return True  # Simplified - would need more sophisticated logic

        except Exception:
            return True  # If we can't parse, assume compatible


class DependencyManager:
    """
    High-level dependency management for the plugin system.

    Coordinates version checking and dependency resolution.
    """

    def __init__(self):
        self.version_checker = VersionChecker()
        self.dependency_resolver = DependencyResolver()

    def validate_plugin(
        self,
        metadata: PluginMetadata,
        auto_install: bool = False
    ) -> Tuple[bool, List[str]]:
        """
        Validate plugin compatibility and dependencies.

        Args:
            metadata: Plugin metadata
            auto_install: If True, attempt to install missing dependencies

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check version compatibility
        is_compatible, error = self.version_checker.check_plugin_metadata(metadata)
        if not is_compatible:
            errors.append(error)

        # Check dependencies
        deps_satisfied, dep_info = self.dependency_resolver.check_dependencies(metadata)

        if not deps_satisfied:
            unsatisfied = [d for d in dep_info if not d.is_satisfied]

            if auto_install:
                logger.info(f"Auto-installing {len(unsatisfied)} missing dependencies...")
                success, install_errors = self.dependency_resolver.install_dependencies(
                    metadata, upgrade=False
                )

                if not success:
                    errors.extend(install_errors)
                else:
                    # Re-check dependencies after installation
                    deps_satisfied, dep_info = self.dependency_resolver.check_dependencies(metadata)
                    if not deps_satisfied:
                        for d in dep_info:
                            if not d.is_satisfied and d.error:
                                errors.append(d.error)
            else:
                for d in unsatisfied:
                    if d.error:
                        errors.append(d.error)

        return len(errors) == 0, errors
