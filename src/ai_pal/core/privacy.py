"""Privacy and PII scrubbing functionality."""

import re
import hashlib
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from loguru import logger


@dataclass
class PIIDetection:
    """Detected PII entity."""

    entity_type: str
    text: str
    start: int
    end: int
    score: float
    anonymized_value: str


@dataclass
class ScrubResult:
    """Result of PII scrubbing operation."""

    original_text: str
    scrubbed_text: str
    detections: List[PIIDetection]
    pii_detected: bool

    def __str__(self) -> str:
        """String representation."""
        if not self.pii_detected:
            return "No PII detected"

        lines = [f"PII Detected: {len(self.detections)} entities"]
        for det in self.detections:
            lines.append(
                f"  - {det.entity_type}: '{det.text}' → '{det.anonymized_value}' "
                f"(confidence: {det.score:.2f})"
            )
        return "\n".join(lines)


class PIIScrubber:
    """Scrubs personally identifiable information from text."""

    def __init__(
        self,
        language: str = "en",
        score_threshold: float = 0.6,
        custom_patterns: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize PII scrubber.

        Args:
            language: Language code (default: "en")
            score_threshold: Minimum confidence score for PII detection
            custom_patterns: Custom regex patterns {entity_type: pattern}
        """
        self.language = language
        self.score_threshold = score_threshold
        self.custom_patterns = custom_patterns or {}

        # Initialize Presidio engines
        logger.info("Initializing PII detection engines...")
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()

        # Entity types to detect
        self.entity_types = [
            "PERSON",
            "EMAIL_ADDRESS",
            "PHONE_NUMBER",
            "CREDIT_CARD",
            "CRYPTO",
            "DATE_TIME",
            "IBAN_CODE",
            "IP_ADDRESS",
            "NRP",  # National Registry of Persons
            "MEDICAL_LICENSE",
            "URL",
            "US_SSN",
            "US_BANK_NUMBER",
            "US_DRIVER_LICENSE",
            "US_ITIN",
            "US_PASSPORT",
            "LOCATION",
            "AGE",
        ]

        # Additional patterns to detect
        self._compile_custom_patterns()

        logger.info(f"PII scrubber initialized (threshold: {score_threshold})")

    def _compile_custom_patterns(self) -> None:
        """Compile custom regex patterns for additional PII detection."""
        # API keys and tokens
        self.api_key_patterns = [
            (r"sk-[a-zA-Z0-9]{48}", "OPENAI_API_KEY"),
            (r"claude-[a-zA-Z0-9]{40,}", "ANTHROPIC_API_KEY"),
            (r"ghp_[a-zA-Z0-9]{36}", "GITHUB_TOKEN"),
            (r"xoxb-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24}", "SLACK_TOKEN"),
            (r"AIza[0-9A-Za-z\\-_]{35}", "GOOGLE_API_KEY"),
            (r"AKIA[0-9A-Z]{16}", "AWS_ACCESS_KEY"),
        ]

        # Cryptocurrency addresses
        self.crypto_patterns = [
            (r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b", "BITCOIN_ADDRESS"),
            (r"\b0x[a-fA-F0-9]{40}\b", "ETHEREUM_ADDRESS"),
        ]

        # Add user-provided custom patterns
        for entity_type, pattern in self.custom_patterns.items():
            self.api_key_patterns.append((pattern, entity_type))

    def _detect_with_regex(self, text: str) -> List[Tuple[str, str, int, int]]:
        """
        Detect PII using custom regex patterns.

        Returns:
            List of (entity_type, matched_text, start, end)
        """
        detections = []

        # Check API keys
        for pattern, entity_type in self.api_key_patterns:
            for match in re.finditer(pattern, text):
                detections.append(
                    (entity_type, match.group(), match.start(), match.end())
                )

        # Check crypto addresses
        for pattern, entity_type in self.crypto_patterns:
            for match in re.finditer(pattern, text):
                detections.append(
                    (entity_type, match.group(), match.start(), match.end())
                )

        return detections

    def _generate_replacement(
        self, entity_type: str, original_value: str
    ) -> str:
        """
        Generate a consistent replacement for PII.

        Uses hashing to ensure same value gets same replacement.
        """
        # Hash the original value
        hash_obj = hashlib.sha256(original_value.encode())
        hash_hex = hash_obj.hexdigest()[:8]

        # Generate replacement based on entity type
        replacements = {
            "PERSON": f"PERSON_{hash_hex}",
            "EMAIL_ADDRESS": f"email_{hash_hex}@example.com",
            "PHONE_NUMBER": f"+1-555-{hash_hex[:4]}",
            "LOCATION": f"LOCATION_{hash_hex}",
            "CREDIT_CARD": f"****-****-****-{hash_hex[:4]}",
            "IP_ADDRESS": f"XXX.XXX.XXX.{int(hash_hex[:2], 16)}",
            "US_SSN": f"***-**-{hash_hex[:4]}",
            "DATE_TIME": "DATE_REDACTED",
            "AGE": "XX",
            "URL": f"https://example.com/{hash_hex}",
        }

        # API keys and tokens
        if "API_KEY" in entity_type or "TOKEN" in entity_type:
            return f"[{entity_type}_{hash_hex}]"

        # Crypto addresses
        if "ADDRESS" in entity_type:
            return f"[{entity_type}_{hash_hex}]"

        return replacements.get(entity_type, f"[{entity_type}_{hash_hex}]")

    def scrub(self, text: str, return_detections: bool = True) -> ScrubResult:
        """
        Scrub PII from text.

        Args:
            text: Input text to scrub
            return_detections: Whether to include detection details

        Returns:
            ScrubResult with scrubbed text and detections
        """
        if not text or not text.strip():
            return ScrubResult(
                original_text=text,
                scrubbed_text=text,
                detections=[],
                pii_detected=False,
            )

        # Analyze with Presidio
        analyzer_results = self.analyzer.analyze(
            text=text,
            language=self.language,
            entities=self.entity_types,
            score_threshold=self.score_threshold,
        )

        # Detect with custom regex patterns
        regex_detections = self._detect_with_regex(text)

        # Combine all detections
        all_detections: List[PIIDetection] = []
        scrubbed_text = text

        # Process Presidio results
        for result in analyzer_results:
            entity_text = text[result.start : result.end]
            replacement = self._generate_replacement(result.entity_type, entity_text)

            if return_detections:
                all_detections.append(
                    PIIDetection(
                        entity_type=result.entity_type,
                        text=entity_text,
                        start=result.start,
                        end=result.end,
                        score=result.score,
                        anonymized_value=replacement,
                    )
                )

        # Use Presidio anonymizer for standard entities
        if analyzer_results:
            operators = {
                entity_type: OperatorConfig("replace", {"new_value": "[REDACTED]"})
                for entity_type in self.entity_types
            }

            anonymized_result = self.anonymizer.anonymize(
                text=text,
                analyzer_results=analyzer_results,
                operators=operators,
            )
            scrubbed_text = anonymized_result.text

        # Apply custom regex replacements
        for entity_type, matched_text, start, end in regex_detections:
            replacement = self._generate_replacement(entity_type, matched_text)
            scrubbed_text = scrubbed_text.replace(matched_text, replacement)

            if return_detections:
                all_detections.append(
                    PIIDetection(
                        entity_type=entity_type,
                        text=matched_text,
                        start=start,
                        end=end,
                        score=1.0,  # Regex matches are high confidence
                        anonymized_value=replacement,
                    )
                )

        result = ScrubResult(
            original_text=text,
            scrubbed_text=scrubbed_text,
            detections=all_detections if return_detections else [],
            pii_detected=len(all_detections) > 0,
        )

        if result.pii_detected:
            logger.debug(f"PII scrubbed: {len(all_detections)} entities detected")

        return result

    def scrub_dict(
        self, data: Dict, keys_to_scrub: Optional[List[str]] = None
    ) -> Dict:
        """
        Scrub PII from dictionary values.

        Args:
            data: Dictionary to scrub
            keys_to_scrub: Specific keys to scrub (None = all string values)

        Returns:
            Dictionary with scrubbed values
        """
        scrubbed = {}

        for key, value in data.items():
            if isinstance(value, str):
                if keys_to_scrub is None or key in keys_to_scrub:
                    result = self.scrub(value, return_detections=False)
                    scrubbed[key] = result.scrubbed_text
                else:
                    scrubbed[key] = value
            elif isinstance(value, dict):
                scrubbed[key] = self.scrub_dict(value, keys_to_scrub)
            elif isinstance(value, list):
                scrubbed[key] = [
                    self.scrub(item, return_detections=False).scrubbed_text
                    if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                scrubbed[key] = value

        return scrubbed

    def is_safe_for_cloud(self, text: str) -> bool:
        """
        Check if text is safe to send to cloud LLMs.

        Returns:
            True if no PII detected, False otherwise
        """
        result = self.scrub(text, return_detections=False)
        return not result.pii_detected


# Global scrubber instance
_scrubber: Optional[PIIScrubber] = None


def get_scrubber() -> PIIScrubber:
    """Get global PII scrubber instance."""
    global _scrubber
    if _scrubber is None:
        _scrubber = PIIScrubber()
    return _scrubber
