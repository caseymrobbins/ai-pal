"""
Gate 2: Extraction Test - Static Analysis

Scans codebase for dark patterns, coercive design, and missing export APIs.
"""

import ast
import sys
from pathlib import Path
from typing import List, Set
from loguru import logger


class DarkPatternDetector(ast.NodeVisitor):
    """AST visitor to detect dark patterns in code."""

    def __init__(self):
        self.violations: List[str] = []
        self.suspicious_patterns: Set[str] = {
            # UI manipulation
            "confirm_shaming",
            "trick_question",
            "hidden_cost",
            "bait_and_switch",
            "forced_continuity",
            # Data extraction
            "sneaking",
            "privacy_zuckering",
            "disguised_ads",
        }

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Check function names and docstrings for dark patterns."""
        func_name_lower = node.name.lower()

        for pattern in self.suspicious_patterns:
            if pattern.replace("_", "") in func_name_lower.replace("_", ""):
                self.violations.append(
                    f"Suspicious function name: {node.name} at line {node.lineno}"
                )

        self.generic_visit(node)


def scan_for_dark_patterns(src_dir: Path) -> List[str]:
    """
    Scan Python files for dark patterns.

    Args:
        src_dir: Source directory to scan

    Returns:
        List of violations found
    """
    logger.info(f"Scanning {src_dir} for dark patterns...")

    violations = []
    detector = DarkPatternDetector()

    for py_file in src_dir.rglob("*.py"):
        try:
            with open(py_file, "r") as f:
                tree = ast.parse(f.read(), filename=str(py_file))
                detector.visit(tree)

                if detector.violations:
                    violations.extend(
                        [f"{py_file}: {v}" for v in detector.violations]
                    )
                    detector.violations = []

        except Exception as e:
            logger.warning(f"Failed to parse {py_file}: {e}")

    return violations


def check_data_portability_apis() -> List[str]:
    """
    Check that all modules with user data have export() methods.

    Returns:
        List of violations
    """
    logger.info("Checking data portability APIs...")

    violations = []

    # Modules that should have export functionality
    data_modules = [
        "ai_pal.modules.personal_data",
        "ai_pal.core.orchestrator",
    ]

    for module_name in data_modules:
        try:
            module = __import__(module_name, fromlist=[""])

            # Check for export-related methods
            has_export = any(
                hasattr(module, name)
                for name in ["export_data", "export_user_data", "download_data"]
            )

            if not has_export:
                violations.append(
                    f"Module {module_name} lacks data export functionality"
                )

        except ImportError:
            violations.append(f"Could not import {module_name}")

    return violations


def main():
    """Run Gate 2 static analysis."""
    logger.info("=" * 80)
    logger.info("GATE 2: EXTRACTION TEST (Static Analysis)")
    logger.info("=" * 80)

    src_dir = Path("src/ai_pal")

    # Check 1: Dark patterns
    dark_pattern_violations = scan_for_dark_patterns(src_dir)

    # Check 2: Data portability
    portability_violations = check_data_portability_apis()

    # Combine violations
    all_violations = dark_pattern_violations + portability_violations

    # Report results
    if all_violations:
        logger.error("❌ GATE 2 FAILED (Static Analysis)")
        for violation in all_violations:
            logger.error(f"  - {violation}")

        exit(1)
    else:
        logger.info("✅ GATE 2 PASSED (Static Analysis)")
        logger.info("  - No dark patterns detected")
        logger.info("  - Data portability APIs present")

        # Create pass flag
        flag_file = Path("reports/gate2_pass.flag")
        flag_file.parent.mkdir(exist_ok=True)
        flag_file.touch()

        exit(0)


if __name__ == "__main__":
    main()
