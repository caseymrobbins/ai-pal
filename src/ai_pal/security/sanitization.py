"""
Input Sanitization and Output Validation

Provides security sanitization for user inputs and validation for system outputs.
"""

import re
import html
import logging
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SanitizationLevel(Enum):
    """Levels of sanitization stringency"""
    STRICT = "strict"  # Maximum security, may break functionality
    MODERATE = "moderate"  # Balanced security and usability
    LENIENT = "lenient"  # Minimal sanitization


@dataclass
class SanitizationResult:
    """Result of sanitization operation"""
    original: str
    sanitized: str
    was_modified: bool
    issues_found: List[str]
    severity: str = "info"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "original_length": len(self.original),
            "sanitized_length": len(self.sanitized),
            "was_modified": self.was_modified,
            "issues_found": self.issues_found,
            "severity": self.severity,
        }


class InputSanitizer:
    """
    Sanitizes user inputs to prevent injection attacks and malicious content.

    Protects against:
    - SQL injection
    - Command injection
    - Path traversal
    - XSS (Cross-Site Scripting)
    - Code injection
    """

    def __init__(self, level: SanitizationLevel = SanitizationLevel.MODERATE):
        self.level = level
        self._dangerous_patterns = self._get_dangerous_patterns()

    def _get_dangerous_patterns(self) -> Dict[str, re.Pattern]:
        """Get patterns for detecting dangerous content"""
        return {
            'sql_injection': re.compile(
                r"('|\"|;|--|\bDROP\b|\bDELETE\b|\bINSERT\b|\bUPDATE\b|\bUNION\b|\bSELECT\b)",
                re.IGNORECASE
            ),
            'command_injection': re.compile(
                r'(\||&&|;|`|\$\(|\${|>|<)',
            ),
            'path_traversal': re.compile(
                r'(\.\./|\.\.\\)',
            ),
            'xss': re.compile(
                r'(<script|<iframe|javascript:|onerror=|onload=)',
                re.IGNORECASE
            ),
            'code_injection': re.compile(
                r'(__import__|exec\(|eval\(|\bimport\s+os\b|\bimport\s+subprocess\b)',
                re.IGNORECASE
            ),
        }

    def sanitize_string(self, input_str: str, context: str = "general") -> SanitizationResult:
        """
        Sanitize a string input.

        Args:
            input_str: String to sanitize
            context: Context of the input (e.g., 'user_id', 'query', 'path')

        Returns:
            SanitizationResult with sanitized string and metadata
        """
        if not input_str:
            return SanitizationResult(
                original=input_str,
                sanitized=input_str,
                was_modified=False,
                issues_found=[],
            )

        original = input_str
        sanitized = input_str
        issues = []

        # Check for dangerous patterns
        for pattern_name, pattern in self._dangerous_patterns.items():
            if pattern.search(sanitized):
                issues.append(f"Detected {pattern_name} pattern")

        # Context-specific sanitization
        if context == "path":
            sanitized = self._sanitize_path(sanitized)
        elif context == "sql":
            sanitized = self._sanitize_sql(sanitized)
        elif context == "html":
            sanitized = self._sanitize_html(sanitized)
        elif context == "command":
            sanitized = self._sanitize_command(sanitized)
        else:
            sanitized = self._sanitize_general(sanitized)

        # Determine severity
        severity = "critical" if issues else "info"

        return SanitizationResult(
            original=original,
            sanitized=sanitized,
            was_modified=(original != sanitized),
            issues_found=issues,
            severity=severity,
        )

    def _sanitize_general(self, text: str) -> str:
        """General-purpose sanitization"""
        # Remove null bytes
        text = text.replace('\x00', '')

        # Limit length based on sanitization level
        max_length = {
            SanitizationLevel.STRICT: 1000,
            SanitizationLevel.MODERATE: 10000,
            SanitizationLevel.LENIENT: 100000,
        }[self.level]

        if len(text) > max_length:
            logger.warning(f"Truncating input from {len(text)} to {max_length} characters")
            text = text[:max_length]

        return text

    def _sanitize_path(self, path: str) -> str:
        """Sanitize file path to prevent directory traversal"""
        # Remove path traversal attempts
        path = re.sub(r'\.\.(/|\\)', '', path)

        # Remove leading slashes (to prevent absolute paths)
        if self.level == SanitizationLevel.STRICT:
            path = path.lstrip('/\\')

        # Remove null bytes
        path = path.replace('\x00', '')

        return path

    def _sanitize_sql(self, text: str) -> str:
        """Sanitize SQL input to prevent SQL injection"""
        # Escape single quotes
        text = text.replace("'", "''")

        # Remove SQL comments
        text = re.sub(r'--.*', '', text)
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)

        # Remove dangerous SQL keywords if strict
        if self.level == SanitizationLevel.STRICT:
            dangerous_keywords = [
                'DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'GRANT', 'REVOKE'
            ]
            for keyword in dangerous_keywords:
                text = re.sub(rf'\b{keyword}\b', '', text, flags=re.IGNORECASE)

        return text

    def _sanitize_html(self, text: str) -> str:
        """Sanitize HTML to prevent XSS"""
        # HTML encode special characters
        text = html.escape(text)

        # Remove javascript: URLs
        text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)

        # Remove dangerous event handlers
        dangerous_events = [
            'onload', 'onerror', 'onclick', 'onmouseover', 'onfocus', 'onblur'
        ]
        for event in dangerous_events:
            text = re.sub(rf'{event}\s*=', '', text, flags=re.IGNORECASE)

        return text

    def _sanitize_command(self, text: str) -> str:
        """Sanitize command input to prevent command injection"""
        # Remove shell metacharacters
        dangerous_chars = ['|', '&', ';', '\n', '`', '$', '>', '<']

        for char in dangerous_chars:
            text = text.replace(char, '')

        # Remove command substitution
        text = re.sub(r'\$\(.*?\)', '', text)
        text = re.sub(r'\${.*?}', '', text)

        return text

    def sanitize_dict(self, data: Dict[str, Any], context: str = "general") -> Dict[str, Any]:
        """
        Sanitize all string values in a dictionary.

        Args:
            data: Dictionary to sanitize
            context: Sanitization context

        Returns:
            Sanitized dictionary
        """
        sanitized = {}

        for key, value in data.items():
            if isinstance(value, str):
                result = self.sanitize_string(value, context)
                sanitized[key] = result.sanitized

                if result.issues_found:
                    logger.warning(
                        f"Sanitization issues in field '{key}': {result.issues_found}"
                    )

            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_dict(value, context)

            elif isinstance(value, list):
                sanitized[key] = [
                    self.sanitize_string(item, context).sanitized if isinstance(item, str) else item
                    for item in value
                ]

            else:
                sanitized[key] = value

        return sanitized


class OutputValidator:
    """
    Validates system outputs for security and content issues.

    Checks for:
    - Secret leakage
    - Sensitive data exposure
    - Malicious content
    - Policy violations
    """

    def __init__(self):
        self._sensitive_patterns = self._get_sensitive_patterns()

    def _get_sensitive_patterns(self) -> Dict[str, re.Pattern]:
        """Get patterns for detecting sensitive data"""
        return {
            'email': re.compile(
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            ),
            'phone': re.compile(
                r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
            ),
            'ssn': re.compile(
                r'\b\d{3}-\d{2}-\d{4}\b'
            ),
            'credit_card': re.compile(
                r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
            ),
            'ip_address': re.compile(
                r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
            ),
        }

    def validate_output(self, output: str, check_secrets: bool = True) -> Dict[str, Any]:
        """
        Validate output for security issues.

        Args:
            output: Output text to validate
            check_secrets: If True, check for leaked secrets

        Returns:
            Validation result dictionary
        """
        issues = []
        warnings = []

        # Check for sensitive data patterns
        for pattern_name, pattern in self._sensitive_patterns.items():
            matches = pattern.findall(output)
            if matches:
                warnings.append(
                    f"Detected {len(matches)} {pattern_name} pattern(s) in output"
                )

        # Check for secrets if requested
        if check_secrets:
            from .secret_scanner import scan_text
            secret_matches = scan_text(output)

            if secret_matches:
                issues.extend([
                    f"Secret detected: {match.secret_type.value} ({match.severity.value})"
                    for match in secret_matches
                ])

        # Check output length
        if len(output) > 1000000:  # 1MB
            warnings.append(f"Output is very large: {len(output)} characters")

        # Determine overall status
        if issues:
            status = "failed"
            severity = "critical"
        elif warnings:
            status = "warning"
            severity = "medium"
        else:
            status = "passed"
            severity = "info"

        return {
            "status": status,
            "severity": severity,
            "issues": issues,
            "warnings": warnings,
            "output_length": len(output),
            "is_safe": len(issues) == 0,
        }

    def redact_sensitive_data(self, text: str) -> Tuple[str, List[str]]:
        """
        Redact sensitive data from text.

        Args:
            text: Text to redact

        Returns:
            Tuple of (redacted_text, list_of_redactions)
        """
        redacted = text
        redactions = []

        # Redact each type of sensitive data
        for pattern_name, pattern in self._sensitive_patterns.items():
            matches = pattern.findall(redacted)

            for match in matches:
                # Redact but keep first few characters
                if len(match) > 4:
                    redacted_value = match[:2] + '*' * (len(match) - 4) + match[-2:]
                else:
                    redacted_value = '*' * len(match)

                redacted = redacted.replace(match, redacted_value)
                redactions.append(f"Redacted {pattern_name}")

        return redacted, redactions


class SecurityValidator:
    """
    Combined security validator for inputs and outputs.

    Provides unified interface for all sanitization and validation operations.
    """

    def __init__(self, sanitization_level: SanitizationLevel = SanitizationLevel.MODERATE):
        self.input_sanitizer = InputSanitizer(level=sanitization_level)
        self.output_validator = OutputValidator()

    def process_input(self, input_data: Any, context: str = "general") -> Any:
        """
        Process and sanitize input data.

        Args:
            input_data: Input to process (string or dict)
            context: Context for sanitization

        Returns:
            Sanitized input
        """
        if isinstance(input_data, str):
            result = self.input_sanitizer.sanitize_string(input_data, context)
            if result.issues_found:
                logger.warning(
                    f"Input sanitization found issues: {result.issues_found}"
                )
            return result.sanitized

        elif isinstance(input_data, dict):
            return self.input_sanitizer.sanitize_dict(input_data, context)

        else:
            return input_data

    def validate_output(self, output: str, allow_sensitive_data: bool = False) -> Dict[str, Any]:
        """
        Validate output for security issues.

        Args:
            output: Output to validate
            allow_sensitive_data: If False, fail on sensitive data

        Returns:
            Validation result
        """
        result = self.output_validator.validate_output(output, check_secrets=True)

        if not allow_sensitive_data and result["warnings"]:
            logger.warning(f"Output validation warnings: {result['warnings']}")

        if not result["is_safe"]:
            logger.error(f"Output validation failed: {result['issues']}")

        return result

    def safe_process(
        self,
        input_data: Any,
        processor_func: Any,
        context: str = "general"
    ) -> Tuple[Any, Dict[str, Any]]:
        """
        Safely process data with input sanitization and output validation.

        Args:
            input_data: Input data to process
            processor_func: Function to process the input
            context: Context for sanitization

        Returns:
            Tuple of (processed_output, validation_result)
        """
        # Sanitize input
        sanitized_input = self.process_input(input_data, context)

        # Process
        output = processor_func(sanitized_input)

        # Validate output
        if isinstance(output, str):
            validation = self.validate_output(output)
        else:
            validation = {"status": "skipped", "is_safe": True}

        return output, validation


# Global validator instance
_validator = None


def get_validator() -> SecurityValidator:
    """Get global validator instance"""
    global _validator
    if _validator is None:
        _validator = SecurityValidator()
    return _validator


def sanitize_input(input_data: Any, context: str = "general") -> Any:
    """Convenience function to sanitize input"""
    return get_validator().process_input(input_data, context)


def validate_output(output: str) -> Dict[str, Any]:
    """Convenience function to validate output"""
    return get_validator().validate_output(output)
