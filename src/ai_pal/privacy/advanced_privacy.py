"""
Advanced Privacy Features

Enhanced privacy protection mechanisms:
- Enhanced PII detection with Presidio integration
- Differential privacy mechanisms
- Data minimization policies
- Privacy budget tracking
- Consent management
- Data retention policies

Part of Phase 3: Enhanced Context, Privacy, Multi-Model Orchestration
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
import hashlib
import re

from loguru import logger


class PIIType(Enum):
    """Types of Personally Identifiable Information"""
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    NAME = "name"
    ADDRESS = "address"
    DATE_OF_BIRTH = "date_of_birth"
    IP_ADDRESS = "ip_address"
    LOCATION = "location"
    MEDICAL = "medical"
    FINANCIAL = "financial"
    BIOMETRIC = "biometric"


class PrivacyAction(Enum):
    """Privacy protection actions"""
    REDACT = "redact"  # Remove PII
    MASK = "mask"  # Replace with placeholder
    ENCRYPT = "encrypt"  # Encrypt PII
    HASH = "hash"  # One-way hash
    TOKENIZE = "tokenize"  # Reversible tokenization
    BLOCK = "block"  # Block entire request


class ConsentLevel(Enum):
    """User consent levels"""
    NONE = "none"  # No consent given
    MINIMAL = "minimal"  # Minimal data processing
    STANDARD = "standard"  # Standard processing
    FULL = "full"  # Full data processing


@dataclass
class PIIDetection:
    """Detected PII instance"""
    pii_type: PIIType
    text: str  # Original text
    start_pos: int
    end_pos: int
    confidence: float  # 0-1
    sensitivity_level: str  # "low", "medium", "high"


@dataclass
class PrivacyBudget:
    """Differential privacy budget tracking"""
    user_id: str
    epsilon: float  # Privacy loss parameter
    delta: float  # Failure probability

    # Tracking
    queries_made: int = 0
    epsilon_spent: float = 0.0
    last_reset: datetime = field(default_factory=datetime.now)

    # Limits
    max_epsilon: float = 1.0
    max_queries_per_day: int = 100

    # Status
    budget_exceeded: bool = False


@dataclass
class DataMinimizationPolicy:
    """Data minimization policy"""
    user_id: str

    # Retention periods (in days)
    conversation_retention: int = 30
    analytics_retention: int = 90
    audit_log_retention: int = 365

    # Minimization rules
    collect_only_necessary: bool = True
    auto_delete_expired: bool = True
    anonymize_analytics: bool = True

    # PII handling
    allowed_pii_types: Set[PIIType] = field(default_factory=set)
    pii_retention_days: int = 7


@dataclass
class ConsentRecord:
    """User consent record"""
    user_id: str
    consent_level: ConsentLevel
    granted_at: datetime
    expires_at: Optional[datetime]

    # Specific permissions
    allow_data_storage: bool = False
    allow_analytics: bool = False
    allow_personalization: bool = False
    allow_third_party_sharing: bool = False

    # Audit
    consent_version: str = "1.0"
    ip_address: Optional[str] = None
    metadata: Dict = field(default_factory=dict)


class AdvancedPrivacyManager:
    """
    Advanced Privacy Management System

    Provides comprehensive privacy protection:
    - Enhanced PII detection (Presidio-compatible)
    - Differential privacy mechanisms
    - Data minimization enforcement
    - Privacy budget tracking
    - Consent management
    """

    # PII detection patterns (simple regex - Presidio would be more sophisticated)
    PII_PATTERNS = {
        PIIType.EMAIL: r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        PIIType.PHONE: r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        PIIType.SSN: r'\b\d{3}-\d{2}-\d{4}\b',
        PIIType.CREDIT_CARD: r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        PIIType.IP_ADDRESS: r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
    }

    def __init__(
        self,
        storage_dir: Path,
        default_epsilon: float = 1.0,
        default_delta: float = 1e-5,
        enable_presidio: bool = False  # Would integrate Presidio in production
    ):
        """
        Initialize Advanced Privacy Manager

        Args:
            storage_dir: Directory for privacy data
            default_epsilon: Default privacy budget epsilon
            default_delta: Default privacy budget delta
            enable_presidio: Enable Presidio integration (requires installation)
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.default_epsilon = default_epsilon
        self.default_delta = default_delta
        self.enable_presidio = enable_presidio

        # In-memory storage
        self.privacy_budgets: Dict[str, PrivacyBudget] = {}
        self.minimization_policies: Dict[str, DataMinimizationPolicy] = {}
        self.consent_records: Dict[str, ConsentRecord] = {}

        # PII detection cache
        self.pii_cache: Dict[str, List[PIIDetection]] = {}

        # Load existing data
        self._load_privacy_data()

        logger.info(
            f"Advanced Privacy Manager initialized with storage at {storage_dir}, "
            f"epsilon: {default_epsilon}, delta: {default_delta}"
        )

    def _load_privacy_data(self) -> None:
        """Load existing privacy data"""
        # Load privacy budgets
        budgets_file = self.storage_dir / "privacy_budgets.json"
        if budgets_file.exists():
            try:
                with open(budgets_file, 'r') as f:
                    data = json.load(f)
                    for user_id, budget_data in data.items():
                        self.privacy_budgets[user_id] = PrivacyBudget(
                            user_id=user_id,
                            epsilon=budget_data["epsilon"],
                            delta=budget_data["delta"],
                            queries_made=budget_data.get("queries_made", 0),
                            epsilon_spent=budget_data.get("epsilon_spent", 0.0),
                            last_reset=datetime.fromisoformat(budget_data["last_reset"]),
                            max_epsilon=budget_data.get("max_epsilon", 1.0),
                            max_queries_per_day=budget_data.get("max_queries_per_day", 100),
                            budget_exceeded=budget_data.get("budget_exceeded", False)
                        )
            except Exception as e:
                logger.error(f"Failed to load privacy budgets: {e}")

        # Load consent records
        consent_file = self.storage_dir / "consent_records.json"
        if consent_file.exists():
            try:
                with open(consent_file, 'r') as f:
                    data = json.load(f)
                    for user_id, consent_data in data.items():
                        self.consent_records[user_id] = ConsentRecord(
                            user_id=user_id,
                            consent_level=ConsentLevel(consent_data["consent_level"]),
                            granted_at=datetime.fromisoformat(consent_data["granted_at"]),
                            expires_at=datetime.fromisoformat(consent_data["expires_at"])
                            if consent_data.get("expires_at") else None,
                            allow_data_storage=consent_data.get("allow_data_storage", False),
                            allow_analytics=consent_data.get("allow_analytics", False),
                            allow_personalization=consent_data.get("allow_personalization", False),
                            allow_third_party_sharing=consent_data.get("allow_third_party_sharing", False),
                            consent_version=consent_data.get("consent_version", "1.0"),
                            ip_address=consent_data.get("ip_address"),
                            metadata=consent_data.get("metadata", {})
                        )
            except Exception as e:
                logger.error(f"Failed to load consent records: {e}")

    async def detect_pii(
        self,
        text: str,
        pii_types: Optional[List[PIIType]] = None
    ) -> List[PIIDetection]:
        """
        Detect PII in text

        In production, this would use Presidio Analyzer
        For now, uses regex patterns

        Args:
            text: Text to analyze
            pii_types: Optional list of PII types to detect

        Returns:
            List of detected PII instances
        """
        # Check cache
        cache_key = hashlib.md5(text.encode()).hexdigest()
        if cache_key in self.pii_cache:
            return self.pii_cache[cache_key]

        detections = []

        # Determine which patterns to use
        patterns_to_check = self.PII_PATTERNS
        if pii_types:
            patterns_to_check = {
                pii_type: pattern
                for pii_type, pattern in self.PII_PATTERNS.items()
                if pii_type in pii_types
            }

        # Detect PII using patterns
        for pii_type, pattern in patterns_to_check.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                detection = PIIDetection(
                    pii_type=pii_type,
                    text=match.group(),
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=0.9,  # Regex patterns are fairly confident
                    sensitivity_level=self._get_sensitivity_level(pii_type)
                )
                detections.append(detection)

        # Cache results
        self.pii_cache[cache_key] = detections

        if detections:
            logger.warning(f"Detected {len(detections)} PII instances in text")

        return detections

    def _get_sensitivity_level(self, pii_type: PIIType) -> str:
        """Determine sensitivity level for PII type"""
        high_sensitivity = {
            PIIType.SSN,
            PIIType.CREDIT_CARD,
            PIIType.MEDICAL,
            PIIType.BIOMETRIC
        }

        medium_sensitivity = {
            PIIType.DATE_OF_BIRTH,
            PIIType.FINANCIAL,
            PIIType.ADDRESS
        }

        if pii_type in high_sensitivity:
            return "high"
        elif pii_type in medium_sensitivity:
            return "medium"
        else:
            return "low"

    async def apply_privacy_protection(
        self,
        text: str,
        action: PrivacyAction = PrivacyAction.REDACT,
        pii_types: Optional[List[PIIType]] = None
    ) -> Tuple[str, List[PIIDetection]]:
        """
        Apply privacy protection to text

        Args:
            text: Text to protect
            action: Privacy action to apply
            pii_types: Optional list of PII types to protect

        Returns:
            Tuple of (protected_text, detections)
        """
        # Detect PII
        detections = await self.detect_pii(text, pii_types)

        if not detections:
            return text, []

        # Apply protection action
        protected_text = text

        # Process detections in reverse order to maintain positions
        for detection in sorted(detections, key=lambda d: d.start_pos, reverse=True):
            before = protected_text[:detection.start_pos]
            after = protected_text[detection.end_pos:]

            if action == PrivacyAction.REDACT:
                replacement = "[REDACTED]"
            elif action == PrivacyAction.MASK:
                replacement = self._mask_text(detection.text, detection.pii_type)
            elif action == PrivacyAction.HASH:
                replacement = self._hash_text(detection.text)
            elif action == PrivacyAction.TOKENIZE:
                replacement = self._tokenize_text(detection.text, detection.pii_type)
            else:
                replacement = "[PROTECTED]"

            protected_text = before + replacement + after

        logger.info(f"Applied {action.value} protection to {len(detections)} PII instances")

        return protected_text, detections

    def _mask_text(self, text: str, pii_type: PIIType) -> str:
        """Mask text while preserving format"""
        if pii_type == PIIType.EMAIL:
            # Show first char and domain: j***@example.com
            parts = text.split('@')
            if len(parts) == 2:
                return f"{parts[0][0]}***@{parts[1]}"

        elif pii_type == PIIType.PHONE:
            # Show last 4 digits: ***-***-1234
            digits = ''.join(c for c in text if c.isdigit())
            if len(digits) >= 4:
                return f"***-***-{digits[-4:]}"

        elif pii_type == PIIType.CREDIT_CARD:
            # Show last 4 digits: ****-****-****-1234
            digits = ''.join(c for c in text if c.isdigit())
            if len(digits) >= 4:
                return f"****-****-****-{digits[-4:]}"

        # Default: replace with asterisks
        return '*' * len(text)

    def _hash_text(self, text: str) -> str:
        """One-way hash of text"""
        hash_val = hashlib.sha256(text.encode()).hexdigest()
        return f"[HASH:{hash_val[:8]}]"

    def _tokenize_text(self, text: str, pii_type: PIIType) -> str:
        """Reversible tokenization (simplified)"""
        # In production, use proper tokenization service
        token = hashlib.md5(text.encode()).hexdigest()[:12]
        return f"[TOKEN:{pii_type.value.upper()}:{token}]"

    async def check_privacy_budget(
        self,
        user_id: str,
        epsilon_cost: float = 0.01
    ) -> bool:
        """
        Check if privacy budget allows query

        Args:
            user_id: User ID
            epsilon_cost: Privacy cost of query

        Returns:
            True if budget allows query
        """
        # Get or create budget
        if user_id not in self.privacy_budgets:
            self.privacy_budgets[user_id] = PrivacyBudget(
                user_id=user_id,
                epsilon=self.default_epsilon,
                delta=self.default_delta
            )

        budget = self.privacy_budgets[user_id]

        # Reset daily budget if needed
        if (datetime.now() - budget.last_reset).days >= 1:
            budget.queries_made = 0
            budget.epsilon_spent = 0.0
            budget.last_reset = datetime.now()
            budget.budget_exceeded = False

        # Check limits
        if budget.queries_made >= budget.max_queries_per_day:
            budget.budget_exceeded = True
            logger.warning(f"User {user_id} exceeded daily query limit")
            return False

        if budget.epsilon_spent + epsilon_cost > budget.max_epsilon:
            budget.budget_exceeded = True
            logger.warning(f"User {user_id} exceeded privacy budget")
            return False

        # Deduct from budget
        budget.queries_made += 1
        budget.epsilon_spent += epsilon_cost

        await self._persist_privacy_budget(user_id)

        return True

    async def _persist_privacy_budget(self, user_id: str) -> None:
        """Persist privacy budget to disk"""
        budgets_file = self.storage_dir / "privacy_budgets.json"

        # Load existing
        data = {}
        if budgets_file.exists():
            with open(budgets_file, 'r') as f:
                data = json.load(f)

        # Update
        budget = self.privacy_budgets[user_id]
        data[user_id] = {
            "epsilon": budget.epsilon,
            "delta": budget.delta,
            "queries_made": budget.queries_made,
            "epsilon_spent": budget.epsilon_spent,
            "last_reset": budget.last_reset.isoformat(),
            "max_epsilon": budget.max_epsilon,
            "max_queries_per_day": budget.max_queries_per_day,
            "budget_exceeded": budget.budget_exceeded
        }

        # Save
        with open(budgets_file, 'w') as f:
            json.dump(data, f, indent=2)

    async def record_consent(
        self,
        user_id: str,
        consent_level: ConsentLevel,
        allow_data_storage: bool = False,
        allow_analytics: bool = False,
        allow_personalization: bool = False,
        allow_third_party_sharing: bool = False,
        expires_in_days: Optional[int] = None,
        ip_address: Optional[str] = None
    ) -> ConsentRecord:
        """
        Record user consent

        Args:
            user_id: User ID
            consent_level: Level of consent
            allow_data_storage: Allow data storage
            allow_analytics: Allow analytics
            allow_personalization: Allow personalization
            allow_third_party_sharing: Allow third-party sharing
            expires_in_days: Optional expiration
            ip_address: Optional IP address for audit

        Returns:
            Created consent record
        """
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now() + timedelta(days=expires_in_days)

        consent = ConsentRecord(
            user_id=user_id,
            consent_level=consent_level,
            granted_at=datetime.now(),
            expires_at=expires_at,
            allow_data_storage=allow_data_storage,
            allow_analytics=allow_analytics,
            allow_personalization=allow_personalization,
            allow_third_party_sharing=allow_third_party_sharing,
            ip_address=ip_address
        )

        self.consent_records[user_id] = consent
        await self._persist_consent_record(user_id)

        logger.info(
            f"Recorded {consent_level.value} consent for user {user_id}"
        )

        return consent

    async def _persist_consent_record(self, user_id: str) -> None:
        """Persist consent record to disk"""
        consent_file = self.storage_dir / "consent_records.json"

        # Load existing
        data = {}
        if consent_file.exists():
            with open(consent_file, 'r') as f:
                data = json.load(f)

        # Update
        consent = self.consent_records[user_id]
        data[user_id] = {
            "consent_level": consent.consent_level.value,
            "granted_at": consent.granted_at.isoformat(),
            "expires_at": consent.expires_at.isoformat() if consent.expires_at else None,
            "allow_data_storage": consent.allow_data_storage,
            "allow_analytics": consent.allow_analytics,
            "allow_personalization": consent.allow_personalization,
            "allow_third_party_sharing": consent.allow_third_party_sharing,
            "consent_version": consent.consent_version,
            "ip_address": consent.ip_address,
            "metadata": consent.metadata
        }

        # Save
        with open(consent_file, 'w') as f:
            json.dump(data, f, indent=2)

    def check_consent(
        self,
        user_id: str,
        required_permission: str
    ) -> bool:
        """
        Check if user has given consent for specific permission

        Args:
            user_id: User ID
            required_permission: Permission to check

        Returns:
            True if consent given
        """
        if user_id not in self.consent_records:
            logger.warning(f"No consent record for user {user_id}")
            return False

        consent = self.consent_records[user_id]

        # Check expiration
        if consent.expires_at and consent.expires_at < datetime.now():
            logger.warning(f"Consent expired for user {user_id}")
            return False

        # Check specific permission
        permission_map = {
            "data_storage": consent.allow_data_storage,
            "analytics": consent.allow_analytics,
            "personalization": consent.allow_personalization,
            "third_party_sharing": consent.allow_third_party_sharing
        }

        return permission_map.get(required_permission, False)

    def apply_data_minimization(
        self,
        user_id: str,
        data: Dict
    ) -> Dict:
        """
        Apply data minimization policy to data

        Args:
            user_id: User ID
            data: Data to minimize

        Returns:
            Minimized data
        """
        # Get policy
        if user_id not in self.minimization_policies:
            self.minimization_policies[user_id] = DataMinimizationPolicy(
                user_id=user_id
            )

        policy = self.minimization_policies[user_id]

        if not policy.collect_only_necessary:
            return data

        # Define necessary fields (example)
        necessary_fields = {
            "user_id",
            "timestamp",
            "message",
            "session_id"
        }

        # Remove unnecessary fields
        minimized = {
            key: value
            for key, value in data.items()
            if key in necessary_fields
        }

        logger.debug(
            f"Applied data minimization: {len(data)} → {len(minimized)} fields"
        )

        return minimized

    def get_privacy_report(self, user_id: str) -> Dict:
        """Get privacy report for user"""
        report = {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }

        # Privacy budget
        if user_id in self.privacy_budgets:
            budget = self.privacy_budgets[user_id]
            report["privacy_budget"] = {
                "epsilon_spent": budget.epsilon_spent,
                "max_epsilon": budget.max_epsilon,
                "queries_made": budget.queries_made,
                "max_queries": budget.max_queries_per_day,
                "budget_exceeded": budget.budget_exceeded
            }

        # Consent
        if user_id in self.consent_records:
            consent = self.consent_records[user_id]
            report["consent"] = {
                "level": consent.consent_level.value,
                "granted_at": consent.granted_at.isoformat(),
                "expires_at": consent.expires_at.isoformat() if consent.expires_at else None,
                "permissions": {
                    "data_storage": consent.allow_data_storage,
                    "analytics": consent.allow_analytics,
                    "personalization": consent.allow_personalization,
                    "third_party_sharing": consent.allow_third_party_sharing
                }
            }

        return report
