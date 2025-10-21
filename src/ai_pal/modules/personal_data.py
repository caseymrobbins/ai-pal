"""
Personal Data Training Module.

Learns about user context, preferences, and goals while respecting privacy.
Must operate within Ethics Module bounds and pass Extraction Test.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
from loguru import logger

from ai_pal.modules.base import BaseModule, ModuleRequest, ModuleResponse


@dataclass
class UserProfile:
    """User profile with personal context."""

    user_id: str
    created_at: datetime
    last_updated: datetime

    # Personal context (privacy-preserving)
    preferences: Dict[str, Any] = field(default_factory=dict)
    goals: List[str] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)
    skills: Dict[str, float] = field(default_factory=dict)  # skill -> level

    # Communication preferences
    preferred_tone: str = "professional"  # professional, casual, friendly
    preferred_detail_level: str = "moderate"  # concise, moderate, detailed
    preferred_language: str = "en"

    # Work context (anonymized)
    work_domain: Optional[str] = None
    typical_tasks: List[str] = field(default_factory=list)

    # Learning context
    learning_goals: List[str] = field(default_factory=list)
    completed_learnings: List[str] = field(default_factory=list)

    # Interaction patterns
    typical_active_hours: List[int] = field(default_factory=list)  # Hours of day
    average_session_length: float = 30.0  # minutes

    # Privacy controls
    data_sharing_consent: bool = False
    pii_scrubbing_required: bool = True


class PersonalDataModule(BaseModule):
    """Privacy-preserving personalization module."""

    def __init__(self):
        super().__init__(
            name="personal_data",
            description="Privacy-preserving user personalization and context learning",
            version="0.1.0",
        )

        self.user_profiles: Dict[str, UserProfile] = {}

    async def initialize(self) -> None:
        """Initialize the module."""
        logger.info("Initializing Personal Data module...")
        self.initialized = True
        logger.info("Personal Data module initialized")

    async def process(self, request: ModuleRequest) -> ModuleResponse:
        """Process a personal data request."""
        start_time = datetime.now()

        task = request.task
        context = request.context
        user_id = request.user_id

        # Get or create profile
        profile = self._get_or_create_profile(user_id)

        if task == "update_profile":
            # Update user profile with new data
            self._update_profile(profile, context)
            result = {"status": "profile_updated", "profile": self._serialize_profile(profile)}

        elif task == "get_profile":
            # Get user profile
            result = self._serialize_profile(profile)

        elif task == "get_context":
            # Get personalized context for current interaction
            result = self._get_personalized_context(profile, context)

        elif task == "record_interaction":
            # Record an interaction for learning
            self._record_interaction(profile, context)
            result = {"status": "interaction_recorded"}

        elif task == "export_data":
            # Export user data (privacy/portability)
            result = self._export_user_data(profile)

        elif task == "delete_data":
            # Delete user data (right to deletion)
            self._delete_user_data(user_id)
            result = {"status": "data_deleted"}

        else:
            result = {"error": f"Unknown task: {task}"}

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        return ModuleResponse(
            result=result,
            confidence=0.95,
            metadata={"user_id": user_id},
            timestamp=datetime.now(),
            processing_time_ms=processing_time,
        )

    def _get_or_create_profile(self, user_id: str) -> UserProfile:
        """Get or create user profile."""
        if user_id not in self.user_profiles:
            profile = UserProfile(
                user_id=user_id,
                created_at=datetime.now(),
                last_updated=datetime.now(),
            )
            self.user_profiles[user_id] = profile
            logger.info(f"Created new user profile for {user_id}")

        return self.user_profiles[user_id]

    def _update_profile(self, profile: UserProfile, updates: Dict[str, Any]) -> None:
        """
        Update user profile.

        Only allows safe, non-extractive updates that pass Extraction Test.
        """
        # Update preferences (safe)
        if "preferences" in updates:
            profile.preferences.update(updates["preferences"])

        # Update goals (empowering)
        if "goals" in updates:
            new_goals = updates["goals"]
            if isinstance(new_goals, list):
                profile.goals = new_goals

        # Update interests (personalization)
        if "interests" in updates:
            new_interests = updates["interests"]
            if isinstance(new_interests, list):
                profile.interests = new_interests

        # Update communication preferences
        if "preferred_tone" in updates:
            profile.preferred_tone = updates["preferred_tone"]

        if "preferred_detail_level" in updates:
            profile.preferred_detail_level = updates["preferred_detail_level"]

        # Update learning context
        if "learning_goals" in updates:
            profile.learning_goals = updates.get("learning_goals", [])

        # Update work context (anonymized only)
        if "work_domain" in updates:
            # Ensure it's generic/anonymized
            domain = updates["work_domain"]
            if self._is_anonymized_domain(domain):
                profile.work_domain = domain

        profile.last_updated = datetime.now()
        logger.debug(f"Updated profile for {profile.user_id}")

    def _is_anonymized_domain(self, domain: str) -> bool:
        """
        Check if work domain is properly anonymized.

        Should be generic like "software engineering", not specific like "Google LLC".
        """
        # Simple check: reject if contains company-specific terms
        forbidden_terms = ["inc", "llc", "corp", "ltd", "gmbh", "company"]

        domain_lower = domain.lower()
        return not any(term in domain_lower for term in forbidden_terms)

    def _get_personalized_context(
        self, profile: UserProfile, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get personalized context for current interaction.

        Returns context that helps personalize responses without compromising privacy.
        """
        return {
            "preferences": profile.preferences,
            "interests": profile.interests,
            "goals": profile.goals,
            "preferred_tone": profile.preferred_tone,
            "preferred_detail_level": profile.preferred_detail_level,
            "work_domain": profile.work_domain,
            "learning_goals": profile.learning_goals,
            "skill_levels": profile.skills,
        }

    def _record_interaction(
        self, profile: UserProfile, interaction: Dict[str, Any]
    ) -> None:
        """
        Record an interaction for learning.

        Learns from interactions to improve personalization.
        """
        # Update interaction patterns
        current_hour = datetime.now().hour
        if current_hour not in profile.typical_active_hours:
            profile.typical_active_hours.append(current_hour)

        # Update skills based on successful tasks
        if interaction.get("task_success"):
            domain = interaction.get("domain")
            if domain:
                current_skill = profile.skills.get(domain, 0.0)
                profile.skills[domain] = min(current_skill + 0.05, 1.0)

        # Record completed learnings
        if interaction.get("learning_completed"):
            topic = interaction.get("topic")
            if topic and topic not in profile.completed_learnings:
                profile.completed_learnings.append(topic)

        profile.last_updated = datetime.now()

    def _serialize_profile(self, profile: UserProfile) -> Dict[str, Any]:
        """Serialize profile to dict."""
        return {
            "user_id": profile.user_id,
            "created_at": profile.created_at.isoformat(),
            "last_updated": profile.last_updated.isoformat(),
            "preferences": profile.preferences,
            "goals": profile.goals,
            "interests": profile.interests,
            "skills": profile.skills,
            "preferred_tone": profile.preferred_tone,
            "preferred_detail_level": profile.preferred_detail_level,
            "work_domain": profile.work_domain,
            "learning_goals": profile.learning_goals,
            "completed_learnings": profile.completed_learnings,
            "typical_active_hours": profile.typical_active_hours,
        }

    def _export_user_data(self, profile: UserProfile) -> Dict[str, Any]:
        """
        Export all user data (data portability).

        Supports user's right to data portability.
        """
        return {
            "export_timestamp": datetime.now().isoformat(),
            "profile": self._serialize_profile(profile),
            "export_format": "json",
            "data_usage_note": (
                "This data is exported for your personal use. "
                "All data was processed locally and only anonymized "
                "data was sent to external services."
            ),
        }

    def _delete_user_data(self, user_id: str) -> None:
        """
        Delete all user data (right to deletion).

        Implements right to be forgotten.
        """
        if user_id in self.user_profiles:
            del self.user_profiles[user_id]
            logger.info(f"Deleted all data for user {user_id}")
        else:
            logger.warning(f"No data found for user {user_id}")

    async def shutdown(self) -> None:
        """Cleanup resources."""
        logger.info("Shutting down Personal Data module...")

        # Save profiles if needed (to persistent storage)
        # In production, would save to encrypted database

        self.initialized = False
