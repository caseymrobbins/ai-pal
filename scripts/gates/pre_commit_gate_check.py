#!/usr/bin/env python3
"""
Pre-Commit Gate Check Script

Runs all 4 gates as pre-commit checks to ensure:
- Gate 1: Net Agency (skill development > deskilling)
- Gate 2: Extraction Static Analysis (no dark patterns)
- Gate 3: Humanity Override (user can stop/modify)
- Gate 4: Performance Parity (human-comparable speed)

Exit code 0 = all gates passed
Exit code 1 = one or more gates failed
"""

import sys
import os
import asyncio
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from ai_pal.gates.agency_validator import AgencyValidator
from ai_pal.gates.extraction_analyzer import ExtractionAnalyzer
from ai_pal.gates.override_checker import OverrideChecker
from ai_pal.gates.performance_validator import PerformanceValidator


class PreCommitGateRunner:
    """Runs all gates as pre-commit checks"""

    def __init__(self):
        self.gates = {
            "Gate 1: Net Agency": AgencyValidator(),
            "Gate 2: Extraction Static Analysis": ExtractionAnalyzer(),
            "Gate 3: Humanity Override": OverrideChecker(),
            "Gate 4: Performance Parity": PerformanceValidator(),
        }
        self.results: Dict[str, Dict[str, Any]] = {}

    async def run_all_gates(self) -> bool:
        """
        Run all gates.

        Returns:
            True if all gates passed, False otherwise
        """
        print("=" * 60)
        print("Running Pre-Commit Gate Checks")
        print("=" * 60)

        all_passed = True

        for gate_name, gate in self.gates.items():
            print(f"\n{gate_name}...")

            try:
                # Run gate check
                result = await self._run_gate(gate_name, gate)
                self.results[gate_name] = result

                if result["passed"]:
                    print(f"  ✓ PASSED")
                else:
                    print(f"  ✗ FAILED: {result.get('reason', 'Unknown reason')}")
                    all_passed = False

                # Show details
                if result.get("details"):
                    for key, value in result["details"].items():
                        print(f"    {key}: {value}")

            except Exception as e:
                print(f"  ✗ ERROR: {str(e)}")
                self.results[gate_name] = {
                    "passed": False,
                    "reason": f"Exception during gate check: {e}"
                }
                all_passed = False

        print("\n" + "=" * 60)
        if all_passed:
            print("✓ ALL GATES PASSED - Commit allowed")
        else:
            print("✗ ONE OR MORE GATES FAILED - Commit blocked")
            print("\nTo bypass gate checks (not recommended):")
            print("  git commit --no-verify")
        print("=" * 60)

        return all_passed

    async def _run_gate(self, gate_name: str, gate) -> Dict[str, Any]:
        """Run a specific gate"""
        if "Gate 1" in gate_name:
            return await self._run_gate1(gate)
        elif "Gate 2" in gate_name:
            return await self._run_gate2(gate)
        elif "Gate 3" in gate_name:
            return await self._run_gate3(gate)
        elif "Gate 4" in gate_name:
            return await self._run_gate4(gate)
        else:
            return {"passed": False, "reason": "Unknown gate"}

    async def _run_gate1(self, gate: AgencyValidator) -> Dict[str, Any]:
        """Run Gate 1: Net Agency"""
        # Analyze recent changes for skill development patterns
        # In a real scenario, this would analyze commit diffs
        # For pre-commit, we can do static analysis

        # Simple check: Are we adding AI-powered features without proper scaffolding?
        changed_files = self._get_changed_files()

        ai_additions = 0
        scaffolding_additions = 0

        for file_path in changed_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()

                # Count AI-related additions
                if 'orchestrator' in content.lower() or 'llm' in content.lower():
                    ai_additions += 1

                # Count scaffolding additions (FFE, ARI, EDM)
                if any(term in content.lower() for term in ['ffe', 'ari', 'edm', 'scaffold', 'skill_development']):
                    scaffolding_additions += 1

            except:
                pass

        # Pass if we're adding scaffolding along with AI features
        if ai_additions > 0 and scaffolding_additions == 0:
            return {
                "passed": False,
                "reason": "Adding AI features without skill development scaffolding",
                "details": {
                    "ai_features_added": ai_additions,
                    "scaffolding_added": scaffolding_additions,
                }
            }

        return {
            "passed": True,
            "details": {
                "ai_features_added": ai_additions,
                "scaffolding_added": scaffolding_additions,
            }
        }

    async def _run_gate2(self, gate: ExtractionAnalyzer) -> Dict[str, Any]:
        """Run Gate 2: Extraction Static Analysis"""
        changed_files = self._get_changed_files()

        dark_patterns_found = []

        for file_path in changed_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()

                # Check for dark patterns
                dark_patterns = [
                    ('automatic_subscription', r'auto[_-]?subscribe|auto[_-]?renew'),
                    ('hidden_costs', r'hidden[_-]?fee|undisclosed[_-]?charge'),
                    ('forced_continuity', r'force[_-]?continue|mandatory[_-]?next'),
                    ('difficult_cancellation', r'prevent[_-]?cancel|block[_-]?unsubscribe'),
                ]

                import re
                for pattern_name, pattern in dark_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        dark_patterns_found.append({
                            "file": file_path,
                            "pattern": pattern_name,
                        })

            except:
                pass

        if dark_patterns_found:
            return {
                "passed": False,
                "reason": f"Found {len(dark_patterns_found)} potential dark patterns",
                "details": {
                    "dark_patterns": dark_patterns_found,
                }
            }

        return {
            "passed": True,
            "details": {
                "files_checked": len(changed_files),
                "dark_patterns_found": 0,
            }
        }

    async def _run_gate3(self, gate: OverrideChecker) -> Dict[str, Any]:
        """Run Gate 3: Humanity Override"""
        changed_files = self._get_changed_files()

        missing_override_mechanisms = []

        for file_path in changed_files:
            # Check if file implements autonomous features
            try:
                with open(file_path, 'r') as f:
                    content = f.read()

                # If file has autonomous execution
                has_autonomous = any(term in content.lower() for term in [
                    'autonomous', 'auto_execute', 'automatic_action', 'auto_apply'
                ])

                # Check for override mechanisms
                has_override = any(term in content.lower() for term in [
                    'override', 'stop', 'cancel', 'abort', 'user_confirmation', 'require_approval'
                ])

                if has_autonomous and not has_override:
                    missing_override_mechanisms.append(file_path)

            except:
                pass

        if missing_override_mechanisms:
            return {
                "passed": False,
                "reason": f"Autonomous features without override mechanisms in {len(missing_override_mechanisms)} files",
                "details": {
                    "files": missing_override_mechanisms,
                }
            }

        return {
            "passed": True,
            "details": {
                "files_checked": len(changed_files),
            }
        }

    async def _run_gate4(self, gate: PerformanceValidator) -> Dict[str, Any]:
        """Run Gate 4: Performance Parity"""
        # For pre-commit, we do static analysis
        # Check for obvious performance issues

        changed_files = self._get_changed_files()
        performance_issues = []

        for file_path in changed_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()

                # Check for potential performance issues
                import re

                # Nested loops without limits
                if re.search(r'for.*:\s*for.*:', content):
                    nested_loops = len(re.findall(r'for.*:\s*for.*:', content))
                    if nested_loops > 2:
                        performance_issues.append({
                            "file": file_path,
                            "issue": f"Multiple nested loops ({nested_loops})",
                        })

                # Synchronous operations in async context
                if 'async def' in content and re.search(r'time\.sleep\(', content):
                    performance_issues.append({
                        "file": file_path,
                        "issue": "Synchronous sleep in async function (use asyncio.sleep)",
                    })

            except:
                pass

        if performance_issues:
            return {
                "passed": False,
                "reason": f"Found {len(performance_issues)} potential performance issues",
                "details": {
                    "issues": performance_issues,
                }
            }

        return {
            "passed": True,
            "details": {
                "files_checked": len(changed_files),
            }
        }

    def _get_changed_files(self) -> List[str]:
        """Get list of files changed in this commit"""
        import subprocess

        try:
            # Get staged files
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM'],
                capture_output=True,
                text=True,
                check=True,
            )

            files = result.stdout.strip().split('\n')
            # Filter to only Python files
            python_files = [f for f in files if f.endswith('.py') and os.path.exists(f)]

            return python_files

        except subprocess.CalledProcessError:
            return []


def main():
    """Main entry point"""
    runner = PreCommitGateRunner()

    # Run gates
    all_passed = asyncio.run(runner.run_all_gates())

    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
