"""
Social Relatedness Module - Privacy-First Win Sharing

Enables users to share their wins with chosen groups for:
- Social connection and belonging
- Mutual encouragement
- Shared celebration of growth

Key Principles:
- USER-INITIATED ONLY: No automatic sharing
- PRIVACY FIRST: Granular privacy controls
- OPT-IN: Default is private
- NO SOCIAL PRESSURE: Can leave groups anytime
- NO METRICS GAMING: No follower counts or likes

Powered by:
- RewardEmitter (generates shareable wins)
- ProgressTapestry (win history)
- Privacy controls (per-win, per-group)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Any
from datetime import datetime
from enum import Enum
import uuid


class PrivacyLevel(str, Enum):
    """Privacy levels for sharing"""
    PRIVATE = "private"          # Only you
    GROUP = "group"              # Specific group(s)
    COMMUNITY = "community"      # All AI-PAL users


class GroupRole(str, Enum):
    """Roles within a group"""
    OWNER = "owner"              # Created the group
    ADMIN = "admin"              # Can manage group
    MEMBER = "member"            # Regular member


@dataclass
class SocialGroup:
    """A user-defined sharing group"""
    group_id: str
    name: str
    description: str
    created_by: str
    created_at: datetime

    # Members
    members: Set[str] = field(default_factory=set)  # user_ids
    member_roles: Dict[str, GroupRole] = field(default_factory=dict)

    # Settings
    is_open: bool = False        # Anyone can join vs invite-only
    allow_win_sharing: bool = True
    allow_comments: bool = True

    # Privacy
    visibility: PrivacyLevel = PrivacyLevel.PRIVATE

    # Metadata
    member_count: int = 0
    total_wins_shared: int = 0


@dataclass
class SharedWin:
    """A win shared with a group"""
    share_id: str
    user_id: str
    win_id: str                  # References RewardEmitter win

    # Content
    win_description: str
    win_type: str                # milestone, goal_completed, discovery, etc.
    celebration_text: str

    # Sharing
    shared_with_groups: List[str] = field(default_factory=list)  # group_ids
    privacy_level: PrivacyLevel = PrivacyLevel.PRIVATE

    # Engagement (optional, user can disable)
    allow_encouragement: bool = True
    encouragements: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata
    shared_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Encouragement:
    """Encouragement from another user"""
    encouragement_id: str
    from_user_id: str
    to_user_id: str
    share_id: str

    # Content
    message: str                 # Simple encouragement message

    # Metadata
    sent_at: datetime = field(default_factory=datetime.utcnow)


class SocialRelatednessModule:
    """
    Social Relatedness Module - Privacy-first win sharing

    Enables users to:
    - Create/join groups of their choosing
    - Share wins with chosen groups (user-initiated only)
    - Give/receive encouragement
    - Build social connection around growth

    Privacy guarantees:
    - No automatic sharing
    - Granular controls per win and per group
    - Can leave groups anytime
    - Can delete shared content anytime
    - No follower counts or social metrics gaming
    """

    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize Social Relatedness Module

        Args:
            storage_dir: Where to persist social data
        """
        self.storage_dir = storage_dir or "./data/social"

        # In-memory storage (would be database in production)
        self._groups: Dict[str, SocialGroup] = {}
        self._shared_wins: Dict[str, SharedWin] = {}
        self._user_groups: Dict[str, Set[str]] = {}  # user_id -> group_ids
        self._group_feeds: Dict[str, List[str]] = {}  # group_id -> share_ids

    # ===== GROUP MANAGEMENT =====

    async def create_group(
        self,
        user_id: str,
        name: str,
        description: str,
        is_open: bool = False,
        allow_comments: bool = True
    ) -> SocialGroup:
        """
        Create a new sharing group

        Args:
            user_id: User creating the group
            name: Group name
            description: Group description
            is_open: Anyone can join (True) vs invite-only (False)
            allow_comments: Allow encouragement messages

        Returns:
            New SocialGroup
        """
        group_id = str(uuid.uuid4())

        group = SocialGroup(
            group_id=group_id,
            name=name,
            description=description,
            created_by=user_id,
            created_at=datetime.utcnow(),
            is_open=is_open,
            allow_comments=allow_comments
        )

        # Add creator as owner
        group.members.add(user_id)
        group.member_roles[user_id] = GroupRole.OWNER
        group.member_count = 1

        # Store
        self._groups[group_id] = group

        # Add to user's groups
        if user_id not in self._user_groups:
            self._user_groups[user_id] = set()
        self._user_groups[user_id].add(group_id)

        # Initialize feed
        self._group_feeds[group_id] = []

        return group

    async def join_group(
        self,
        user_id: str,
        group_id: str
    ) -> bool:
        """
        Join an open group or accept an invitation

        Args:
            user_id: User joining
            group_id: Group to join

        Returns:
            True if joined successfully
        """
        if group_id not in self._groups:
            raise ValueError(f"Group {group_id} not found")

        group = self._groups[group_id]

        # Check if group is open or user is invited
        if not group.is_open:
            # Would check invitation system here
            return False

        # Add user to group
        group.members.add(user_id)
        group.member_roles[user_id] = GroupRole.MEMBER
        group.member_count = len(group.members)

        # Add to user's groups
        if user_id not in self._user_groups:
            self._user_groups[user_id] = set()
        self._user_groups[user_id].add(group_id)

        return True

    async def leave_group(
        self,
        user_id: str,
        group_id: str
    ) -> bool:
        """
        Leave a group

        User can leave anytime - no social pressure.

        Args:
            user_id: User leaving
            group_id: Group to leave

        Returns:
            True if left successfully
        """
        if group_id not in self._groups:
            return False

        group = self._groups[group_id]

        # Remove from group
        if user_id in group.members:
            group.members.remove(user_id)
            if user_id in group.member_roles:
                del group.member_roles[user_id]
            group.member_count = len(group.members)

        # Remove from user's groups
        if user_id in self._user_groups:
            self._user_groups[user_id].discard(group_id)

        return True

    async def get_user_groups(
        self,
        user_id: str
    ) -> List[SocialGroup]:
        """
        Get all groups a user is in

        Args:
            user_id: User to get groups for

        Returns:
            List of SocialGroups
        """
        if user_id not in self._user_groups:
            return []

        group_ids = self._user_groups[user_id]
        groups = [
            self._groups[gid]
            for gid in group_ids
            if gid in self._groups
        ]

        return groups

    # ===== WIN SHARING =====

    async def share_win(
        self,
        user_id: str,
        win_id: str,
        win_description: str,
        win_type: str,
        celebration_text: str,
        share_with_groups: List[str],
        allow_encouragement: bool = True
    ) -> SharedWin:
        """
        Share a win with chosen groups (USER-INITIATED)

        Args:
            user_id: User sharing the win
            win_id: ID from RewardEmitter
            win_description: What was accomplished
            win_type: Type of win
            celebration_text: Celebration message
            share_with_groups: List of group_ids to share with
            allow_encouragement: Allow others to send encouragement

        Returns:
            SharedWin object
        """
        share_id = str(uuid.uuid4())

        # Verify user is in all specified groups
        user_groups = self._user_groups.get(user_id, set())
        for group_id in share_with_groups:
            if group_id not in user_groups:
                raise ValueError(f"User not in group {group_id}")

        # Determine privacy level
        if not share_with_groups:
            privacy_level = PrivacyLevel.PRIVATE
        else:
            privacy_level = PrivacyLevel.GROUP

        # Create shared win
        shared_win = SharedWin(
            share_id=share_id,
            user_id=user_id,
            win_id=win_id,
            win_description=win_description,
            win_type=win_type,
            celebration_text=celebration_text,
            shared_with_groups=share_with_groups,
            privacy_level=privacy_level,
            allow_encouragement=allow_encouragement
        )

        # Store
        self._shared_wins[share_id] = shared_win

        # Add to group feeds
        for group_id in share_with_groups:
            if group_id in self._group_feeds:
                self._group_feeds[group_id].append(share_id)

            # Increment group stats
            if group_id in self._groups:
                self._groups[group_id].total_wins_shared += 1

        return shared_win

    async def unshare_win(
        self,
        user_id: str,
        share_id: str
    ) -> bool:
        """
        Remove a shared win

        User can delete shared content anytime.

        Args:
            user_id: User who shared it
            share_id: Share to remove

        Returns:
            True if removed successfully
        """
        if share_id not in self._shared_wins:
            return False

        shared_win = self._shared_wins[share_id]

        # Verify ownership
        if shared_win.user_id != user_id:
            return False

        # Remove from group feeds
        for group_id in shared_win.shared_with_groups:
            if group_id in self._group_feeds:
                if share_id in self._group_feeds[group_id]:
                    self._group_feeds[group_id].remove(share_id)

        # Delete
        del self._shared_wins[share_id]

        return True

    async def get_group_feed(
        self,
        group_id: str,
        user_id: str,
        limit: int = 20
    ) -> List[SharedWin]:
        """
        Get recent wins shared in a group

        Args:
            group_id: Group to get feed for
            user_id: User requesting feed (must be member)
            limit: Max wins to return

        Returns:
            List of SharedWin objects
        """
        # Verify user is in group
        if user_id not in self._user_groups.get(group_id, set()):
            user_groups = self._user_groups.get(user_id, set())
            if group_id not in user_groups:
                raise ValueError("User not in group")

        # Get feed
        if group_id not in self._group_feeds:
            return []

        share_ids = self._group_feeds[group_id][-limit:]  # Recent wins

        wins = [
            self._shared_wins[sid]
            for sid in reversed(share_ids)  # Newest first
            if sid in self._shared_wins
        ]

        return wins

    # ===== ENCOURAGEMENT =====

    async def send_encouragement(
        self,
        from_user_id: str,
        to_user_id: str,
        share_id: str,
        message: str
    ) -> Encouragement:
        """
        Send encouragement to someone's shared win

        Args:
            from_user_id: User sending encouragement
            to_user_id: User receiving it
            share_id: Win being encouraged
            message: Encouragement message

        Returns:
            Encouragement object
        """
        if share_id not in self._shared_wins:
            raise ValueError(f"Share {share_id} not found")

        shared_win = self._shared_wins[share_id]

        # Check if encouragement is allowed
        if not shared_win.allow_encouragement:
            raise ValueError("Encouragement not allowed on this win")

        # Create encouragement
        encouragement_id = str(uuid.uuid4())
        encouragement = Encouragement(
            encouragement_id=encouragement_id,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            share_id=share_id,
            message=message
        )

        # Add to shared win
        shared_win.encouragements.append({
            "from_user_id": from_user_id,
            "message": message,
            "sent_at": encouragement.sent_at.isoformat()
        })

        return encouragement

    # ===== PRIVACY CONTROLS =====

    async def update_win_privacy(
        self,
        user_id: str,
        share_id: str,
        new_groups: List[str],
        allow_encouragement: Optional[bool] = None
    ) -> SharedWin:
        """
        Update privacy settings for a shared win

        Args:
            user_id: User who shared it
            share_id: Share to update
            new_groups: New list of groups to share with
            allow_encouragement: Update encouragement setting

        Returns:
            Updated SharedWin
        """
        if share_id not in self._shared_wins:
            raise ValueError(f"Share {share_id} not found")

        shared_win = self._shared_wins[share_id]

        # Verify ownership
        if shared_win.user_id != user_id:
            raise ValueError("Not your win to update")

        # Remove from old groups
        for old_group_id in shared_win.shared_with_groups:
            if old_group_id not in new_groups:
                if old_group_id in self._group_feeds:
                    if share_id in self._group_feeds[old_group_id]:
                        self._group_feeds[old_group_id].remove(share_id)

        # Add to new groups
        for new_group_id in new_groups:
            if new_group_id not in shared_win.shared_with_groups:
                if new_group_id in self._group_feeds:
                    self._group_feeds[new_group_id].append(share_id)

        # Update
        shared_win.shared_with_groups = new_groups

        if allow_encouragement is not None:
            shared_win.allow_encouragement = allow_encouragement

        return shared_win

    # ===== STATISTICS (Opt-in, no gaming) =====

    async def get_user_stats(
        self,
        user_id: str,
        include_in_response: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get user's social stats (opt-in only)

        No follower counts or social metrics gaming.
        Just simple stats if user wants them.

        Args:
            user_id: User to get stats for
            include_in_response: User has opted in to see stats

        Returns:
            Stats dict if opted in, None otherwise
        """
        if not include_in_response:
            return None

        # Count shared wins
        user_shares = [
            sw for sw in self._shared_wins.values()
            if sw.user_id == user_id
        ]

        # Count encouragements received
        encouragements_received = sum(
            len(sw.encouragements)
            for sw in user_shares
        )

        return {
            "groups_joined": len(self._user_groups.get(user_id, set())),
            "wins_shared": len(user_shares),
            "encouragements_received": encouragements_received,
        }
