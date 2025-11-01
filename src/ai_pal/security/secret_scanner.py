"""
Secret Scanner

Comprehensive secret detection system for identifying sensitive information
in code, configurations, responses, and data.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class SecretType(Enum):
    """Types of secrets that can be detected"""
    API_KEY = "api_key"
    AWS_KEY = "aws_access_key"
    AWS_SECRET = "aws_secret_key"
    PRIVATE_KEY = "private_key"
    PASSWORD = "password"
    TOKEN = "token"
    DATABASE_URL = "database_url"
    OAUTH_SECRET = "oauth_secret"
    CRYPTO_KEY = "crypto_key"
    CERTIFICATE = "certificate"
    JWT = "jwt"
    SSH_KEY = "ssh_key"
    GENERIC_SECRET = "generic_secret"


class SecretSeverity(Enum):
    """Severity levels for detected secrets"""
    CRITICAL = "critical"  # Active credentials that grant access
    HIGH = "high"  # Likely real secrets
    MEDIUM = "medium"  # Possible secrets
    LOW = "low"  # Low confidence matches
    INFO = "info"  # Informational only


@dataclass
class SecretMatch:
    """Information about a detected secret"""
    secret_type: SecretType
    severity: SecretSeverity
    matched_text: str  # Redacted version
    line_number: Optional[int] = None
    column: Optional[int] = None
    file_path: Optional[str] = None
    context: Optional[str] = None  # Surrounding text
    confidence: float = 1.0  # 0.0 to 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "secret_type": self.secret_type.value,
            "severity": self.severity.value,
            "matched_text": self.matched_text,
            "line_number": self.line_number,
            "column": self.column,
            "file_path": self.file_path,
            "context": self.context,
            "confidence": self.confidence,
        }


class SecretPattern:
    """Pattern definition for secret detection"""

    def __init__(
        self,
        name: str,
        secret_type: SecretType,
        pattern: str,
        severity: SecretSeverity = SecretSeverity.HIGH,
        confidence: float = 0.9,
        description: str = "",
    ):
        self.name = name
        self.secret_type = secret_type
        self.pattern = re.compile(pattern, re.IGNORECASE)
        self.severity = severity
        self.confidence = confidence
        self.description = description


class SecretScanner:
    """
    Scans text, files, and data structures for secrets and sensitive information.

    Uses pattern matching and entropy analysis to detect:
    - API keys
    - Access tokens
    - Private keys
    - Passwords
    - Database credentials
    - And more...
    """

    def __init__(self):
        self.patterns: List[SecretPattern] = []
        self._initialize_patterns()
        self._false_positive_indicators = self._get_false_positive_indicators()

    def _initialize_patterns(self) -> None:
        """Initialize secret detection patterns"""

        # API Keys - Generic patterns
        self.patterns.extend([
            SecretPattern(
                name="Generic API Key",
                secret_type=SecretType.API_KEY,
                pattern=r'(?:api[_-]?key|apikey)["\']?\s*[:=]\s*["\']?([a-z0-9_\-]{32,})',
                severity=SecretSeverity.HIGH,
                confidence=0.8,
            ),
            SecretPattern(
                name="Bearer Token",
                secret_type=SecretType.TOKEN,
                pattern=r'bearer\s+([a-z0-9_\-\.]{20,})',
                severity=SecretSeverity.HIGH,
                confidence=0.9,
            ),
        ])

        # AWS Keys
        self.patterns.extend([
            SecretPattern(
                name="AWS Access Key ID",
                secret_type=SecretType.AWS_KEY,
                pattern=r'(AKIA[0-9A-Z]{16})',
                severity=SecretSeverity.CRITICAL,
                confidence=0.95,
            ),
            SecretPattern(
                name="AWS Secret Access Key",
                secret_type=SecretType.AWS_SECRET,
                pattern=r'aws[_-]?secret[_-]?access[_-]?key["\']?\s*[:=]\s*["\']?([a-z0-9/+=]{40})',
                severity=SecretSeverity.CRITICAL,
                confidence=0.9,
            ),
        ])

        # Anthropic API Keys
        self.patterns.append(
            SecretPattern(
                name="Anthropic API Key",
                secret_type=SecretType.API_KEY,
                pattern=r'(sk-ant-[a-z0-9\-_]{95,})',
                severity=SecretSeverity.CRITICAL,
                confidence=0.99,
            )
        )

        # OpenAI API Keys
        self.patterns.append(
            SecretPattern(
                name="OpenAI API Key",
                secret_type=SecretType.API_KEY,
                pattern=r'(sk-[a-zA-Z0-9]{48})',
                severity=SecretSeverity.CRITICAL,
                confidence=0.95,
            )
        )

        # GitHub Tokens
        self.patterns.extend([
            SecretPattern(
                name="GitHub Personal Access Token",
                secret_type=SecretType.TOKEN,
                pattern=r'(ghp_[a-zA-Z0-9]{36})',
                severity=SecretSeverity.CRITICAL,
                confidence=0.99,
            ),
            SecretPattern(
                name="GitHub OAuth Token",
                secret_type=SecretType.OAUTH_SECRET,
                pattern=r'(gho_[a-zA-Z0-9]{36})',
                severity=SecretSeverity.CRITICAL,
                confidence=0.99,
            ),
        ])

        # Private Keys
        self.patterns.extend([
            SecretPattern(
                name="RSA Private Key",
                secret_type=SecretType.PRIVATE_KEY,
                pattern=r'-----BEGIN RSA PRIVATE KEY-----',
                severity=SecretSeverity.CRITICAL,
                confidence=1.0,
            ),
            SecretPattern(
                name="SSH Private Key",
                secret_type=SecretType.SSH_KEY,
                pattern=r'-----BEGIN OPENSSH PRIVATE KEY-----',
                severity=SecretSeverity.CRITICAL,
                confidence=1.0,
            ),
            SecretPattern(
                name="PGP Private Key",
                secret_type=SecretType.PRIVATE_KEY,
                pattern=r'-----BEGIN PGP PRIVATE KEY BLOCK-----',
                severity=SecretSeverity.CRITICAL,
                confidence=1.0,
            ),
        ])

        # Database URLs
        self.patterns.extend([
            SecretPattern(
                name="PostgreSQL Connection String",
                secret_type=SecretType.DATABASE_URL,
                pattern=r'postgresql://[^:]+:[^@]+@[^/]+/\w+',
                severity=SecretSeverity.CRITICAL,
                confidence=0.95,
            ),
            SecretPattern(
                name="MySQL Connection String",
                secret_type=SecretType.DATABASE_URL,
                pattern=r'mysql://[^:]+:[^@]+@[^/]+/\w+',
                severity=SecretSeverity.CRITICAL,
                confidence=0.95,
            ),
            SecretPattern(
                name="MongoDB Connection String",
                secret_type=SecretType.DATABASE_URL,
                pattern=r'mongodb(\+srv)?://[^:]+:[^@]+@[^/]+',
                severity=SecretSeverity.CRITICAL,
                confidence=0.95,
            ),
        ])

        # JWT Tokens
        self.patterns.append(
            SecretPattern(
                name="JWT Token",
                secret_type=SecretType.JWT,
                pattern=r'(eyJ[a-zA-Z0-9_\-]+\.eyJ[a-zA-Z0-9_\-]+\.[a-zA-Z0-9_\-]+)',
                severity=SecretSeverity.HIGH,
                confidence=0.9,
            )
        )

        # Passwords
        self.patterns.extend([
            SecretPattern(
                name="Password in URL",
                secret_type=SecretType.PASSWORD,
                pattern=r'://[^:]+:([^@]{8,})@',
                severity=SecretSeverity.HIGH,
                confidence=0.85,
            ),
            SecretPattern(
                name="Password Assignment",
                secret_type=SecretType.PASSWORD,
                pattern=r'password["\']?\s*[:=]\s*["\']([^"\']{8,})["\']',
                severity=SecretSeverity.MEDIUM,
                confidence=0.7,
            ),
        ])

        # Generic secrets
        self.patterns.extend([
            SecretPattern(
                name="Generic Secret",
                secret_type=SecretType.GENERIC_SECRET,
                pattern=r'(?:secret|token|key)["\']?\s*[:=]\s*["\']([a-z0-9_\-]{20,})["\']',
                severity=SecretSeverity.MEDIUM,
                confidence=0.6,
            ),
        ])

    def _get_false_positive_indicators(self) -> Set[str]:
        """Get set of indicators for false positives"""
        return {
            'example', 'sample', 'test', 'demo', 'placeholder', 'your_key_here',
            'xxx', 'yyy', 'zzz', 'abc', '123', 'fake', 'dummy', 'mock',
            'todo', 'fixme', '<key>', '{key}', '$key', '${key}',
        }

    def scan_text(self, text: str, context: str = None) -> List[SecretMatch]:
        """
        Scan text for secrets.

        Args:
            text: Text to scan
            context: Optional context (e.g., filename)

        Returns:
            List of detected secrets
        """
        matches = []
        lines = text.split('\n')

        for line_num, line in enumerate(lines, 1):
            line_matches = self._scan_line(line, line_num, context)
            matches.extend(line_matches)

        # Filter false positives
        matches = self._filter_false_positives(matches)

        return matches

    def _scan_line(
        self,
        line: str,
        line_num: int,
        context: Optional[str]
    ) -> List[SecretMatch]:
        """Scan a single line for secrets"""
        matches = []

        for pattern in self.patterns:
            for match in pattern.pattern.finditer(line):
                # Extract matched text
                matched_text = match.group(0)

                # Redact the actual secret
                if len(match.groups()) > 0:
                    secret_value = match.group(1)
                    redacted = self._redact_secret(secret_value)
                    matched_text = matched_text.replace(secret_value, redacted)

                # Get column position
                column = match.start()

                secret_match = SecretMatch(
                    secret_type=pattern.secret_type,
                    severity=pattern.severity,
                    matched_text=matched_text,
                    line_number=line_num,
                    column=column,
                    context=context,
                    confidence=pattern.confidence,
                )

                matches.append(secret_match)

        return matches

    def _redact_secret(self, secret: str, reveal_chars: int = 4) -> str:
        """
        Redact a secret, showing only first few characters.

        Args:
            secret: Secret to redact
            reveal_chars: Number of characters to reveal

        Returns:
            Redacted secret
        """
        if len(secret) <= reveal_chars:
            return '*' * len(secret)

        return secret[:reveal_chars] + '*' * (len(secret) - reveal_chars)

    def _filter_false_positives(self, matches: List[SecretMatch]) -> List[SecretMatch]:
        """Filter out likely false positives"""
        filtered = []

        for match in matches:
            is_false_positive = False

            # Check for false positive indicators
            matched_lower = match.matched_text.lower()
            for indicator in self._false_positive_indicators:
                if indicator in matched_lower:
                    is_false_positive = True
                    logger.debug(
                        f"Filtering false positive: {match.matched_text} "
                        f"(contains '{indicator}')"
                    )
                    break

            # Check entropy (real secrets typically have high entropy)
            if not is_false_positive:
                entropy = self._calculate_entropy(match.matched_text)
                if entropy < 2.5:  # Low entropy = likely not a real secret
                    is_false_positive = True
                    logger.debug(
                        f"Filtering low-entropy match: {match.matched_text} "
                        f"(entropy: {entropy:.2f})"
                    )

            if not is_false_positive:
                filtered.append(match)

        return filtered

    def _calculate_entropy(self, text: str) -> float:
        """
        Calculate Shannon entropy of text.

        Args:
            text: Text to analyze

        Returns:
            Entropy value (higher = more random)
        """
        import math

        if not text:
            return 0.0

        # Count character frequencies
        char_counts: Dict[str, int] = {}
        for char in text:
            char_counts[char] = char_counts.get(char, 0) + 1

        # Calculate entropy
        length = len(text)
        entropy = 0.0

        for count in char_counts.values():
            probability = count / length
            entropy -= probability * math.log2(probability)

        return entropy

    def scan_file(self, file_path: Path) -> List[SecretMatch]:
        """
        Scan a file for secrets.

        Args:
            file_path: Path to file

        Returns:
            List of detected secrets
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            return self.scan_text(content, context=str(file_path))

        except Exception as e:
            logger.error(f"Error scanning file {file_path}: {e}")
            return []

    def scan_directory(
        self,
        directory: Path,
        recursive: bool = True,
        exclude_patterns: Optional[List[str]] = None
    ) -> Dict[str, List[SecretMatch]]:
        """
        Scan a directory for secrets.

        Args:
            directory: Directory to scan
            recursive: If True, scan subdirectories
            exclude_patterns: File patterns to exclude (e.g., ["*.pyc", "node_modules/*"])

        Returns:
            Dictionary mapping file paths to detected secrets
        """
        results = {}
        exclude_patterns = exclude_patterns or [
            "*.pyc", "*.pyo", "*.so", "*.dylib", "*.egg-info/*",
            ".git/*", ".venv/*", "venv/*", "node_modules/*",
            "__pycache__/*", "*.min.js", "*.min.css"
        ]

        # Get files to scan
        if recursive:
            files = []
            for pattern in ["**/*.py", "**/*.json", "**/*.yaml", "**/*.yml", "**/*.env", "**/*.txt"]:
                files.extend(directory.glob(pattern))
        else:
            files = list(directory.glob("*"))

        # Filter out excluded files
        files = [f for f in files if f.is_file() and not self._should_exclude(f, exclude_patterns)]

        # Scan each file
        for file_path in files:
            matches = self.scan_file(file_path)
            if matches:
                results[str(file_path)] = matches

        return results

    def _should_exclude(self, file_path: Path, exclude_patterns: List[str]) -> bool:
        """Check if file matches any exclude pattern"""
        import fnmatch

        for pattern in exclude_patterns:
            if fnmatch.fnmatch(str(file_path), pattern):
                return True

        return False

    def scan_dict(self, data: Dict[str, Any], path: str = "") -> List[SecretMatch]:
        """
        Recursively scan a dictionary for secrets.

        Args:
            data: Dictionary to scan
            path: Current path in the dictionary (for context)

        Returns:
            List of detected secrets
        """
        matches = []

        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key

            if isinstance(value, str):
                # Scan string values
                line_matches = self.scan_text(value, context=current_path)
                matches.extend(line_matches)

            elif isinstance(value, dict):
                # Recursively scan nested dictionaries
                nested_matches = self.scan_dict(value, current_path)
                matches.extend(nested_matches)

            elif isinstance(value, list):
                # Scan list items
                for i, item in enumerate(value):
                    if isinstance(item, str):
                        item_matches = self.scan_text(item, context=f"{current_path}[{i}]")
                        matches.extend(item_matches)
                    elif isinstance(item, dict):
                        item_matches = self.scan_dict(item, f"{current_path}[{i}]")
                        matches.extend(item_matches)

        return matches


# Global scanner instance
_scanner = None


def get_scanner() -> SecretScanner:
    """Get global scanner instance"""
    global _scanner
    if _scanner is None:
        _scanner = SecretScanner()
    return _scanner


def scan_text(text: str) -> List[SecretMatch]:
    """Convenience function to scan text"""
    return get_scanner().scan_text(text)


def scan_file(file_path: Path) -> List[SecretMatch]:
    """Convenience function to scan file"""
    return get_scanner().scan_file(file_path)
