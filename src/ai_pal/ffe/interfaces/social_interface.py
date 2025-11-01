"""
Social Interface - User-Facing Social Features

Provides interface for:
- Creating and managing groups
- Sharing wins with chosen groups
- Viewing group feeds
- Sending/receiving encouragement

Always user-initiated, privacy-first design.
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from ..modules.social import (
    SocialRelatednessModule,
    SocialGroup,
    SharedWin,
    Encouragement,
    PrivacyLevel,
    GroupRole,
)


@dataclass
class GroupSuggestion:
    """Suggestion for creating a group"""
    suggested_name: str
    suggested_description: str
    reason: str              # Why this group might be useful
    suggested_members: List[str] = None  # Optional


class SocialInterface:
    """
    Social Interface - User-facing social features

    Provides simple, privacy-first social connection.

    Design principles:
    - User must initiate all sharing
    - Clear privacy controls
    - No pressure to participate
    - Can leave/delete anytime
    - No gaming of social metrics
    """

    def __init__(self, social_module: SocialRelatednessModule):
        """
        Initialize Social Interface

        Args:
            social_module: SocialRelatednessModule backend
        """
        self.social = social_module

    # ===== GROUP MANAGEMENT =====

    async def create_group(
        self,
        user_id: str,
        name: str,
        description: str,
        is_open: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new sharing group

        Args:
            user_id: User creating the group
            name: Group name
            description: What the group is for
            is_open: Anyone can join (True) or invite-only (False)

        Returns:
            Group info
        """
        group = await self.social.create_group(
            user_id=user_id,
            name=name,
            description=description,
            is_open=is_open
        )

        return {
            "group_id": group.group_id,
            "name": group.name,
            "description": group.description,
            "created_at": group.created_at.isoformat(),
            "is_open": group.is_open,
            "member_count": group.member_count,
            "your_role": "owner"
        }

    async def join_group(
        self,
        user_id: str,
        group_id: str
    ) -> Dict[str, Any]:
        """
        Join an open group

        Args:
            user_id: User joining
            group_id: Group to join

        Returns:
            Join result
        """
        success = await self.social.join_group(user_id, group_id)

        if success:
            group = self.social._groups.get(group_id)
            return {
                "success": True,
                "message": f"You joined {group.name}!",
                "group": {
                    "name": group.name,
                    "description": group.description,
                    "member_count": group.member_count
                }
            }
        else:
            return {
                "success": False,
                "message": "Unable to join group (may be invite-only)"
            }

    async def leave_group(
        self,
        user_id: str,
        group_id: str
    ) -> Dict[str, Any]:
        """
        Leave a group (no pressure)

        Args:
            user_id: User leaving
            group_id: Group to leave

        Returns:
            Leave confirmation
        """
        success = await self.social.leave_group(user_id, group_id)

        if success:
            return {
                "success": True,
                "message": "You left the group. You can rejoin anytime."
            }
        else:
            return {
                "success": False,
                "message": "Group not found"
            }

    async def list_my_groups(
        self,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        List all groups user is in

        Args:
            user_id: User to list groups for

        Returns:
            List of group summaries
        """
        groups = await self.social.get_user_groups(user_id)

        return [
            {
                "group_id": g.group_id,
                "name": g.name,
                "description": g.description,
                "member_count": g.member_count,
                "total_wins_shared": g.total_wins_shared,
                "your_role": g.member_roles.get(user_id, GroupRole.MEMBER).value
            }
            for g in groups
        ]

    # ===== WIN SHARING =====

    async def share_win_prompt(
        self,
        user_id: str,
        win_description: str
    ) -> Dict[str, Any]:
        """
        Prompt user if they want to share a win

        USER-INITIATED: We ask, user decides.

        Args:
            user_id: User who achieved the win
            win_description: What they accomplished

        Returns:
            Sharing prompt with options
        """
        # Get user's groups
        groups = await self.social.get_user_groups(user_id)

        return {
            "win_description": win_description,
            "prompt": "Want to share this win with your groups?",
            "options": {
                "share": "Yes, share with selected groups",
                "private": "Keep it private (just for me)",
                "later": "Ask me later"
            },
            "available_groups": [
                {
                    "group_id": g.group_id,
                    "name": g.name,
                    "member_count": g.member_count
                }
                for g in groups
            ]
        }

    async def share_win(
        self,
        user_id: str,
        win_id: str,
        win_description: str,
        win_type: str,
        celebration_text: str,
        selected_groups: List[str],
        allow_encouragement: bool = True
    ) -> Dict[str, Any]:
        """
        Share a win with selected groups (user chose to share)

        Args:
            user_id: User sharing
            win_id: Win ID from RewardEmitter
            win_description: What was accomplished
            win_type: Type of win
            celebration_text: Celebration message
            selected_groups: Groups user chose to share with
            allow_encouragement: Allow others to encourage

        Returns:
            Share confirmation
        """
        shared_win = await self.social.share_win(
            user_id=user_id,
            win_id=win_id,
            win_description=win_description,
            win_type=win_type,
            celebration_text=celebration_text,
            share_with_groups=selected_groups,
            allow_encouragement=allow_encouragement
        )

        group_names = [
            self.social._groups[gid].name
            for gid in selected_groups
            if gid in self.social._groups
        ]

        return {
            "share_id": shared_win.share_id,
            "shared_with": group_names,
            "message": f"Your win was shared with {len(selected_groups)} group(s)!",
            "can_unshare": True,
            "can_change_privacy": True
        }

    async def unshare_win(
        self,
        user_id: str,
        share_id: str
    ) -> Dict[str, Any]:
        """
        Remove a shared win (user can delete anytime)

        Args:
            user_id: User who shared it
            share_id: Share to remove

        Returns:
            Removal confirmation
        """
        success = await self.social.unshare_win(user_id, share_id)

        if success:
            return {
                "success": True,
                "message": "Win removed from groups"
            }
        else:
            return {
                "success": False,
                "message": "Could not remove win"
            }

    # ===== GROUP FEED =====

    async def view_group_feed(
        self,
        user_id: str,
        group_id: str,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        View wins shared in a group

        Args:
            user_id: User viewing (must be member)
            group_id: Group to view
            limit: Max wins to show

        Returns:
            Feed with wins
        """
        group = self.social._groups.get(group_id)
        if not group:
            return {"error": "Group not found"}

        wins = await self.social.get_group_feed(group_id, user_id, limit)

        return {
            "group_name": group.name,
            "group_description": group.description,
            "member_count": group.member_count,
            "wins": [
                {
                    "share_id": w.share_id,
                    "user_id": w.user_id,  # Would be replaced with username
                    "win_description": w.win_description,
                    "celebration_text": w.celebration_text,
                    "shared_at": w.shared_at.isoformat(),
                    "encouragements_count": len(w.encouragements),
                    "can_encourage": w.allow_encouragement and w.user_id != user_id
                }
                for w in wins
            ]
        }

    # ===== ENCOURAGEMENT =====

    async def send_encouragement(
        self,
        from_user_id: str,
        share_id: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Send encouragement to someone's win

        Args:
            from_user_id: User sending encouragement
            share_id: Win to encourage
            message: Encouragement message

        Returns:
            Send confirmation
        """
        shared_win = self.social._shared_wins.get(share_id)
        if not shared_win:
            return {"error": "Win not found"}

        encouragement = await self.social.send_encouragement(
            from_user_id=from_user_id,
            to_user_id=shared_win.user_id,
            share_id=share_id,
            message=message
        )

        return {
            "success": True,
            "message": "Encouragement sent!",
            "sent_at": encouragement.sent_at.isoformat()
        }

    # ===== PRIVACY CONTROLS =====

    async def update_win_privacy(
        self,
        user_id: str,
        share_id: str,
        new_groups: List[str],
        allow_encouragement: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Update who can see a shared win

        Args:
            user_id: User updating
            share_id: Win to update
            new_groups: New list of groups
            allow_encouragement: Update encouragement setting

        Returns:
            Update confirmation
        """
        updated_win = await self.social.update_win_privacy(
            user_id=user_id,
            share_id=share_id,
            new_groups=new_groups,
            allow_encouragement=allow_encouragement
        )

        return {
            "success": True,
            "message": "Privacy settings updated",
            "now_shared_with": len(new_groups),
            "allow_encouragement": updated_win.allow_encouragement
        }

    # ===== HELPER METHODS =====

    async def suggest_groups(
        self,
        user_id: str,
        based_on_goals: Optional[List[str]] = None
    ) -> List[GroupSuggestion]:
        """
        Suggest groups user might want to create/join

        Args:
            user_id: User to suggest for
            based_on_goals: Optional list of user's goals

        Returns:
            List of group suggestions
        """
        suggestions = []

        # Example suggestions (would be more sophisticated in production)
        if based_on_goals:
            for goal in based_on_goals[:3]:
                suggestions.append(GroupSuggestion(
                    suggested_name=f"{goal} Learners",
                    suggested_description=f"A group for people learning {goal}",
                    reason=f"You're working on '{goal}' - connect with others!"
                ))

        # Generic suggestions
        suggestions.extend([
            GroupSuggestion(
                suggested_name="Daily Wins",
                suggested_description="Share your daily progress and wins",
                reason="Celebrate small daily victories together"
            ),
            GroupSuggestion(
                suggested_name="Accountability Partners",
                suggested_description="Keep each other on track",
                reason="Mutual support for staying consistent"
            )
        ])

        return suggestions

    async def get_social_stats(
        self,
        user_id: str,
        show_stats: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Get social stats (opt-in only)

        Args:
            user_id: User to get stats for
            show_stats: User opted in to see stats

        Returns:
            Stats if opted in, None otherwise
        """
        return await self.social.get_user_stats(
            user_id=user_id,
            include_in_response=show_stats
        )
