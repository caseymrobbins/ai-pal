"""
EDM (Epistemic Debt Monitoring) System with Fact-Checking

Monitors and prevents accumulation of epistemic debt:
- Unfalsifiable claims
- Unverified assertions
- Missing citations
- Circular reasoning
- Outdated information

Enhanced with automated fact-checking integration.

Part of Phase 2: Advanced Monitoring & Self-Improvement
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
import re
import os

import httpx
from loguru import logger


class DebtSeverity(Enum):
    """Epistemic debt severity levels"""
    LOW = "low"  # Minor unverified claim
    MEDIUM = "medium"  # Significant unverified assertion
    HIGH = "high"  # Critical claim without evidence
    CRITICAL = "critical"  # Dangerous misinformation


class FactCheckStatus(Enum):
    """Fact-checking result status"""
    VERIFIED = "verified"  # Claim verified as true
    DISPUTED = "disputed"  # Claim has conflicting evidence
    FALSE = "false"  # Claim verified as false
    UNVERIFIABLE = "unverifiable"  # Cannot be verified
    PENDING = "pending"  # Awaiting fact-check


@dataclass
class EpistemicDebtSnapshot:
    """Single epistemic debt instance"""
    debt_id: str
    timestamp: datetime
    claim: str  # The claim being made
    context: str  # Surrounding context
    task_id: str
    user_id: str

    # Debt Classification
    severity: DebtSeverity
    debt_type: str  # "unfalsifiable", "unverified", "citation_missing", etc.

    # Fact-Checking
    fact_check_status: FactCheckStatus = FactCheckStatus.PENDING
    fact_check_source: Optional[str] = None
    fact_check_evidence: Optional[str] = None
    fact_check_confidence: float = 0.0  # 0-1

    # Resolution
    resolved: bool = False
    resolution_method: Optional[str] = None  # "citation_added", "claim_retracted", etc.
    resolution_timestamp: Optional[datetime] = None

    metadata: Dict = field(default_factory=dict)


@dataclass
class EDMReport:
    """Epistemic Debt Monitoring Report"""
    period_start: datetime
    period_end: datetime
    user_id: Optional[str] = None

    # Aggregate Metrics
    total_debt_instances: int = 0
    resolved_debt: int = 0
    pending_debt: int = 0
    verified_claims: int = 0
    false_claims: int = 0

    # By Severity
    debt_by_severity: Dict[str, int] = field(default_factory=dict)

    # Trends
    debt_accumulation_rate: float = 0.0  # Debts per day
    resolution_rate: float = 0.0  # % of debt resolved
    fact_check_accuracy: float = 0.0  # % of fact-checks verified

    # Alerts
    alerts: List[str] = field(default_factory=list)
    high_risk_claims: List[EpistemicDebtSnapshot] = field(default_factory=list)


class EDMMonitor:
    """
    Epistemic Debt Monitoring System

    Detects and tracks epistemic debt patterns:
    - Unfalsifiable claims (cannot be proven true/false)
    - Unverified assertions (lack evidence/citation)
    - Circular reasoning
    - Outdated information
    - Missing context

    Integrates with fact-checking APIs for automated verification.
    """

    # Patterns that indicate epistemic debt
    UNFALSIFIABLE_PATTERNS = [
        r"everyone knows",
        r"it's obvious that",
        r"clearly,",
        r"undeniably",
        r"without a doubt",
        r"no one can deny",
    ]

    UNVERIFIED_PATTERNS = [
        r"studies show",
        r"research indicates",
        r"experts say",
        r"it has been proven",
        r"statistics show",
    ]

    VAGUE_PATTERNS = [
        r"many people",
        r"some say",
        r"it is believed",
        r"generally speaking",
    ]

    def __init__(
        self,
        storage_dir: Path,
        fact_check_enabled: bool = True,
        auto_resolve_verified: bool = True,
        max_unresolved_debt: int = 50,
        google_fact_check_api_key: Optional[str] = None
    ):
        """
        Initialize EDM Monitor

        Args:
            storage_dir: Directory for storing debt snapshots
            fact_check_enabled: Enable automatic fact-checking
            auto_resolve_verified: Auto-resolve verified claims
            max_unresolved_debt: Alert if unresolved debt exceeds this
            google_fact_check_api_key: Google Fact Check Tools API key
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.fact_check_enabled = fact_check_enabled
        self.auto_resolve_verified = auto_resolve_verified
        self.max_unresolved_debt = max_unresolved_debt

        # API configuration
        self.google_fact_check_api_key = google_fact_check_api_key or os.getenv("GOOGLE_FACT_CHECK_API_KEY")

        # In-memory cache
        self.debt_instances: Dict[str, EpistemicDebtSnapshot] = {}
        self.user_debt: Dict[str, List[str]] = {}  # user_id -> list of debt_ids

        # Load existing debt
        self._load_debt_instances()

        logger.info(
            f"EDM Monitor initialized with storage at {storage_dir}, "
            f"fact-checking: {fact_check_enabled}, "
            f"max unresolved: {max_unresolved_debt}, "
            f"Google API configured: {bool(self.google_fact_check_api_key)}"
        )

    def _load_debt_instances(self) -> None:
        """Load existing debt instances from storage"""
        debt_files = list(self.storage_dir.glob("*.json"))
        logger.info(f"Loading {len(debt_files)} debt instance files")

        for debt_file in debt_files:
            try:
                with open(debt_file, 'r') as f:
                    data = json.load(f)
                    debt = EpistemicDebtSnapshot(
                        debt_id=data["debt_id"],
                        timestamp=datetime.fromisoformat(data["timestamp"]),
                        claim=data["claim"],
                        context=data["context"],
                        task_id=data["task_id"],
                        user_id=data["user_id"],
                        severity=DebtSeverity(data["severity"]),
                        debt_type=data["debt_type"],
                        fact_check_status=FactCheckStatus(data["fact_check_status"]),
                        fact_check_source=data.get("fact_check_source"),
                        fact_check_evidence=data.get("fact_check_evidence"),
                        fact_check_confidence=data.get("fact_check_confidence", 0.0),
                        resolved=data.get("resolved", False),
                        resolution_method=data.get("resolution_method"),
                        resolution_timestamp=datetime.fromisoformat(data["resolution_timestamp"])
                        if data.get("resolution_timestamp") else None,
                        metadata=data.get("metadata", {})
                    )

                    self.debt_instances[debt.debt_id] = debt

                    # Track by user
                    if debt.user_id not in self.user_debt:
                        self.user_debt[debt.user_id] = []
                    self.user_debt[debt.user_id].append(debt.debt_id)

            except Exception as e:
                logger.error(f"Failed to load debt instance {debt_file}: {e}")

    async def analyze_text(
        self,
        text: str,
        task_id: str,
        user_id: str,
        context: str = ""
    ) -> List[EpistemicDebtSnapshot]:
        """
        Analyze text for epistemic debt patterns

        Args:
            text: Text to analyze
            task_id: Associated task ID
            user_id: User ID
            context: Additional context

        Returns:
            List of detected epistemic debt instances
        """
        detected_debts = []

        # Check for unfalsifiable claims
        for pattern in self.UNFALSIFIABLE_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                debt = await self._create_debt_instance(
                    claim=self._extract_claim(text, match.start(), match.end()),
                    context=context or text,
                    task_id=task_id,
                    user_id=user_id,
                    debt_type="unfalsifiable",
                    severity=DebtSeverity.MEDIUM
                )
                detected_debts.append(debt)

        # Check for unverified assertions
        for pattern in self.UNVERIFIED_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Check if citation follows
                has_citation = self._has_citation_nearby(text, match.end())

                if not has_citation:
                    debt = await self._create_debt_instance(
                        claim=self._extract_claim(text, match.start(), match.end()),
                        context=context or text,
                        task_id=task_id,
                        user_id=user_id,
                        debt_type="missing_citation",
                        severity=DebtSeverity.HIGH
                    )
                    detected_debts.append(debt)

        # Check for vague claims
        for pattern in self.VAGUE_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                debt = await self._create_debt_instance(
                    claim=self._extract_claim(text, match.start(), match.end()),
                    context=context or text,
                    task_id=task_id,
                    user_id=user_id,
                    debt_type="vague_claim",
                    severity=DebtSeverity.LOW
                )
                detected_debts.append(debt)

        # Trigger fact-checking if enabled
        if self.fact_check_enabled:
            for debt in detected_debts:
                if debt.severity in [DebtSeverity.HIGH, DebtSeverity.CRITICAL]:
                    asyncio.create_task(self._fact_check_claim(debt))

        logger.info(f"Detected {len(detected_debts)} epistemic debt instances in text")
        return detected_debts

    async def _create_debt_instance(
        self,
        claim: str,
        context: str,
        task_id: str,
        user_id: str,
        debt_type: str,
        severity: DebtSeverity
    ) -> EpistemicDebtSnapshot:
        """Create and store a debt instance"""
        debt_id = f"{user_id}_{task_id}_{datetime.now().timestamp()}"

        debt = EpistemicDebtSnapshot(
            debt_id=debt_id,
            timestamp=datetime.now(),
            claim=claim,
            context=context,
            task_id=task_id,
            user_id=user_id,
            severity=severity,
            debt_type=debt_type
        )

        # Store in memory
        self.debt_instances[debt_id] = debt

        if user_id not in self.user_debt:
            self.user_debt[user_id] = []
        self.user_debt[user_id].append(debt_id)

        # Persist to disk
        await self._persist_debt(debt)

        # Check for alerts
        await self._check_debt_alerts(user_id)

        return debt

    async def _persist_debt(self, debt: EpistemicDebtSnapshot) -> None:
        """Persist debt instance to storage"""
        filepath = self.storage_dir / f"{debt.debt_id}.json"

        try:
            with open(filepath, 'w') as f:
                json.dump({
                    "debt_id": debt.debt_id,
                    "timestamp": debt.timestamp.isoformat(),
                    "claim": debt.claim,
                    "context": debt.context,
                    "task_id": debt.task_id,
                    "user_id": debt.user_id,
                    "severity": debt.severity.value,
                    "debt_type": debt.debt_type,
                    "fact_check_status": debt.fact_check_status.value,
                    "fact_check_source": debt.fact_check_source,
                    "fact_check_evidence": debt.fact_check_evidence,
                    "fact_check_confidence": debt.fact_check_confidence,
                    "resolved": debt.resolved,
                    "resolution_method": debt.resolution_method,
                    "resolution_timestamp": debt.resolution_timestamp.isoformat()
                    if debt.resolution_timestamp else None,
                    "metadata": debt.metadata
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist debt {debt.debt_id}: {e}")

    async def _fact_check_claim(self, debt: EpistemicDebtSnapshot) -> None:
        """
        Perform fact-checking on a claim using multiple sources:
        1. Google Fact Check Tools API (if API key available)
        2. Wikipedia API for basic verification
        3. Heuristic fallback for pattern matching

        Integrates with real fact-checking services.
        """
        logger.info(f"Fact-checking claim: {debt.claim[:100]}...")

        # Try Google Fact Check Tools API first
        if self.google_fact_check_api_key:
            try:
                result = await self._check_google_fact_check_api(debt.claim)
                if result:
                    debt.fact_check_status = result["status"]
                    debt.fact_check_source = result["source"]
                    debt.fact_check_evidence = result["evidence"]
                    debt.fact_check_confidence = result["confidence"]
                    await self._persist_debt(debt)

                    if self.auto_resolve_verified and debt.fact_check_status == FactCheckStatus.VERIFIED:
                        await self.resolve_debt(debt.debt_id, "auto_verified")
                    return
            except Exception as e:
                logger.warning(f"Google Fact Check API failed: {e}, trying fallback methods")

        # Try Wikipedia API as fallback
        try:
            result = await self._check_wikipedia_api(debt.claim)
            if result:
                debt.fact_check_status = result["status"]
                debt.fact_check_source = result["source"]
                debt.fact_check_evidence = result["evidence"]
                debt.fact_check_confidence = result["confidence"]
                await self._persist_debt(debt)

                if self.auto_resolve_verified and debt.fact_check_status == FactCheckStatus.VERIFIED:
                    await self.resolve_debt(debt.debt_id, "auto_verified")
                return
        except Exception as e:
            logger.warning(f"Wikipedia API failed: {e}, using heuristic fallback")

        # Fallback to heuristic analysis
        await self._heuristic_fact_check(debt)
        await self._persist_debt(debt)

        # Auto-resolve if verified and enabled
        if self.auto_resolve_verified and debt.fact_check_status == FactCheckStatus.VERIFIED:
            await self.resolve_debt(debt.debt_id, "auto_verified")

    async def _check_google_fact_check_api(self, claim: str) -> Optional[Dict]:
        """
        Check claim using Google Fact Check Tools API

        Returns dict with status, source, evidence, confidence or None
        """
        url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
        params = {
            "query": claim,
            "key": self.google_fact_check_api_key,
            "languageCode": "en"
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data.get("claims"):
                return None

            # Get the first claim review
            claim_review = data["claims"][0]
            reviews = claim_review.get("claimReview", [])

            if not reviews:
                return None

            # Analyze the review rating
            review = reviews[0]
            rating = review.get("textualRating", "").lower()

            # Map rating to our status
            if any(word in rating for word in ["true", "correct", "accurate"]):
                status = FactCheckStatus.VERIFIED
                confidence = 0.9
            elif any(word in rating for word in ["false", "incorrect", "inaccurate"]):
                status = FactCheckStatus.FALSE
                confidence = 0.9
            elif any(word in rating for word in ["disputed", "mixed", "partly"]):
                status = FactCheckStatus.DISPUTED
                confidence = 0.7
            else:
                status = FactCheckStatus.UNVERIFIABLE
                confidence = 0.5

            return {
                "status": status,
                "source": f"Google Fact Check - {review.get('publisher', {}).get('name', 'Unknown')}",
                "evidence": f"{rating}: {review.get('text', 'No details available')}",
                "confidence": confidence
            }

    async def _check_wikipedia_api(self, claim: str) -> Optional[Dict]:
        """
        Check claim against Wikipedia for basic verification

        Returns dict with status, source, evidence, confidence or None
        """
        # Extract key terms from claim for search
        search_terms = " ".join([
            word for word in claim.split()
            if len(word) > 4 and word.lower() not in ["that", "this", "with", "from"]
        ][:5])

        if not search_terms:
            return None

        # Search Wikipedia
        search_url = "https://en.wikipedia.org/w/api.php"
        search_params = {
            "action": "opensearch",
            "search": search_terms,
            "limit": 3,
            "format": "json"
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(search_url, params=search_params)
            response.raise_for_status()
            data = response.json()

            if len(data) < 4 or not data[1]:
                return None

            # Get the first result's description
            title = data[1][0]
            description = data[2][0] if data[2] else ""
            url = data[3][0] if data[3] else ""

            # Simple relevance check
            claim_lower = claim.lower()
            if any(term.lower() in claim_lower for term in title.split()):
                return {
                    "status": FactCheckStatus.VERIFIED,
                    "source": f"Wikipedia - {title}",
                    "evidence": f"Found relevant article: {description[:200]}... (See: {url})",
                    "confidence": 0.6
                }

            return {
                "status": FactCheckStatus.UNVERIFIABLE,
                "source": "Wikipedia",
                "evidence": "No directly relevant Wikipedia articles found",
                "confidence": 0.4
            }

    async def _heuristic_fact_check(self, debt: EpistemicDebtSnapshot) -> None:
        """
        Heuristic-based fact checking using pattern matching
        """
        claim_lower = debt.claim.lower()

        # Check for vague citations
        if "studies show" in claim_lower or "research indicates" in claim_lower:
            debt.fact_check_status = FactCheckStatus.UNVERIFIABLE
            debt.fact_check_confidence = 0.3
            debt.fact_check_evidence = "Claim requires specific citation to verify"

        # Check for absolute statements
        elif any(word in claim_lower for word in ["everyone", "no one", "always", "never"]):
            debt.fact_check_status = FactCheckStatus.DISPUTED
            debt.fact_check_confidence = 0.6
            debt.fact_check_evidence = "Absolute claims are rarely accurate without qualification"

        # Check for weasel words
        elif any(pattern.replace(r"\b", "").replace(r"\\", "") in claim_lower
                 for pattern in self.VAGUE_PATTERNS):
            debt.fact_check_status = FactCheckStatus.UNVERIFIABLE
            debt.fact_check_confidence = 0.4
            debt.fact_check_evidence = "Vague attribution reduces verifiability"

        # Default: pending further review
        else:
            debt.fact_check_status = FactCheckStatus.PENDING
            debt.fact_check_confidence = 0.5
            debt.fact_check_evidence = "Requires manual verification or additional context"

    async def resolve_debt(
        self,
        debt_id: str,
        resolution_method: str,
        notes: str = ""
    ) -> bool:
        """
        Resolve an epistemic debt instance

        Args:
            debt_id: ID of debt to resolve
            resolution_method: How it was resolved
            notes: Additional notes

        Returns:
            True if resolved successfully
        """
        if debt_id not in self.debt_instances:
            logger.warning(f"Debt {debt_id} not found")
            return False

        debt = self.debt_instances[debt_id]
        debt.resolved = True
        debt.resolution_method = resolution_method
        debt.resolution_timestamp = datetime.now()

        if notes:
            debt.metadata["resolution_notes"] = notes

        await self._persist_debt(debt)

        logger.info(f"Resolved debt {debt_id} via {resolution_method}")
        return True

    def _extract_claim(self, text: str, start: int, end: int, context_chars: int = 200) -> str:
        """Extract claim with surrounding context"""
        # Find sentence boundaries
        claim_start = max(0, text.rfind('.', max(0, start - context_chars), start) + 1)
        claim_end = text.find('.', end, min(len(text), end + context_chars))
        if claim_end == -1:
            claim_end = min(len(text), end + context_chars)

        return text[claim_start:claim_end].strip()

    def _has_citation_nearby(self, text: str, position: int, lookhead: int = 100) -> bool:
        """Check if citation appears near position"""
        search_text = text[position:min(len(text), position + lookhead)]

        # Look for citation patterns
        citation_patterns = [
            r'\[\d+\]',  # [1]
            r'\([A-Z][a-z]+,?\s+\d{4}\)',  # (Author, 2020)
            r'doi:',
            r'http[s]?://',
        ]

        for pattern in citation_patterns:
            if re.search(pattern, search_text):
                return True

        return False

    async def _check_debt_alerts(self, user_id: str) -> None:
        """Check if user has excessive unresolved debt"""
        if user_id not in self.user_debt:
            return

        user_debts = [
            self.debt_instances[debt_id]
            for debt_id in self.user_debt[user_id]
            if not self.debt_instances[debt_id].resolved
        ]

        if len(user_debts) > self.max_unresolved_debt:
            logger.warning(
                f"⚠️ User {user_id} has {len(user_debts)} unresolved epistemic debts "
                f"(threshold: {self.max_unresolved_debt})"
            )

        # Check for critical debt
        critical_debts = [d for d in user_debts if d.severity == DebtSeverity.CRITICAL]
        if critical_debts:
            logger.error(
                f"🚨 User {user_id} has {len(critical_debts)} CRITICAL epistemic debts!"
            )

    def generate_report(
        self,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> EDMReport:
        """Generate EDM report"""
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=7)

        # Filter debts
        if user_id:
            relevant_debt_ids = self.user_debt.get(user_id, [])
            debts = [self.debt_instances[debt_id] for debt_id in relevant_debt_ids]
        else:
            debts = list(self.debt_instances.values())

        # Filter by date range
        period_debts = [
            d for d in debts
            if start_date <= d.timestamp <= end_date
        ]

        # Calculate metrics
        total_debt = len(period_debts)
        resolved = sum(1 for d in period_debts if d.resolved)
        pending = total_debt - resolved

        verified = sum(
            1 for d in period_debts
            if d.fact_check_status == FactCheckStatus.VERIFIED
        )
        false = sum(
            1 for d in period_debts
            if d.fact_check_status == FactCheckStatus.FALSE
        )

        # By severity
        debt_by_severity = {}
        for severity in DebtSeverity:
            debt_by_severity[severity.value] = sum(
                1 for d in period_debts if d.severity == severity
            )

        # Rates
        days = (end_date - start_date).days or 1
        accumulation_rate = total_debt / days
        resolution_rate = (resolved / total_debt * 100) if total_debt > 0 else 0.0

        fact_checked = sum(
            1 for d in period_debts
            if d.fact_check_status != FactCheckStatus.PENDING
        )
        fact_check_accuracy = (verified / fact_checked * 100) if fact_checked > 0 else 0.0

        # High risk claims
        high_risk = [
            d for d in period_debts
            if d.severity in [DebtSeverity.HIGH, DebtSeverity.CRITICAL]
            and not d.resolved
        ]

        # Alerts
        alerts = []
        if pending > self.max_unresolved_debt:
            alerts.append(f"⚠️ {pending} unresolved debts (threshold: {self.max_unresolved_debt})")

        if false > 0:
            alerts.append(f"🚨 {false} claims verified as FALSE")

        if debt_by_severity.get(DebtSeverity.CRITICAL.value, 0) > 0:
            alerts.append(f"🚨 {debt_by_severity[DebtSeverity.CRITICAL.value]} CRITICAL severity debts")

        return EDMReport(
            period_start=start_date,
            period_end=end_date,
            user_id=user_id,
            total_debt_instances=total_debt,
            resolved_debt=resolved,
            pending_debt=pending,
            verified_claims=verified,
            false_claims=false,
            debt_by_severity=debt_by_severity,
            debt_accumulation_rate=accumulation_rate,
            resolution_rate=resolution_rate,
            fact_check_accuracy=fact_check_accuracy,
            alerts=alerts,
            high_risk_claims=high_risk
        )
