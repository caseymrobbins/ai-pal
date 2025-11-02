"""
Database Storage Backend - SQLAlchemy Integration

Provides persistent storage for:
- ARI snapshots and trends
- EDM debt instances
- FFE goals and atomic blocks
- User profiles and personality data
- Momentum loop history
- Progress tapestry entries

Supports:
- SQLite for local development
- PostgreSQL for production
- Async operations with asyncio
- Connection pooling
- Query optimization
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
import json

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Index
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.pool import QueuePool, NullPool
from loguru import logger

Base = declarative_base()


# ============================================================================
# Database Models
# ============================================================================

class ARISnapshotDB(Base):
    """ARI snapshot storage"""
    __tablename__ = "ari_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(String(36), unique=True, nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)

    # ARI dimensions
    decision_quality = Column(Float, nullable=False)
    skill_development = Column(Float, nullable=False)
    ai_reliance = Column(Float, nullable=False)
    bottleneck_resolution = Column(Float, nullable=False)
    user_confidence = Column(Float, nullable=False)
    engagement = Column(Float, nullable=False)
    autonomy_perception = Column(Float, nullable=False)

    # Computed metrics
    autonomy_retention = Column(Float, nullable=False)
    delta_agency = Column(Float, nullable=False)

    # Context
    task_description = Column(Text, nullable=True)
    task_complexity = Column(String(50), nullable=True)

    # Indexes for common queries
    __table_args__ = (
        Index('idx_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_ari_score', 'autonomy_retention'),
    )


class EDMDebtDB(Base):
    """Epistemic debt storage"""
    __tablename__ = "edm_debts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    debt_id = Column(String(36), unique=True, nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)

    # Debt details
    claim = Column(Text, nullable=False)
    debt_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False, index=True)
    confidence_score = Column(Float, nullable=False)

    # Context
    source_response = Column(Text, nullable=True)
    task_context = Column(Text, nullable=True)

    # Resolution
    resolved = Column(Boolean, default=False, index=True)
    resolution_date = Column(DateTime, nullable=True)
    resolution_method = Column(String(100), nullable=True)

    __table_args__ = (
        Index('idx_user_unresolved', 'user_id', 'resolved'),
        Index('idx_severity_unresolved', 'severity', 'resolved'),
    )


class GoalDB(Base):
    """FFE goal storage"""
    __tablename__ = "ffe_goals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    goal_id = Column(String(36), unique=True, nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    # Goal details
    description = Column(Text, nullable=False)
    importance = Column(Integer, nullable=False)
    complexity_level = Column(String(50), nullable=False)
    estimated_value = Column(Float, nullable=True)

    # Status
    status = Column(String(50), default="active", index=True)
    completed_at = Column(DateTime, nullable=True)
    deadline = Column(DateTime, nullable=True)

    # Relationships
    atomic_blocks = relationship("AtomicBlockDB", back_populates="goal", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_user_status', 'user_id', 'status'),
    )


class AtomicBlockDB(Base):
    """Atomic block storage"""
    __tablename__ = "atomic_blocks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    block_id = Column(String(36), unique=True, nullable=False, index=True)
    goal_id = Column(String(36), ForeignKey('ffe_goals.goal_id'), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)

    # Block details
    description = Column(Text, nullable=False)
    block_index = Column(Integer, nullable=False)
    size = Column(String(20), nullable=False)
    estimated_minutes = Column(Integer, nullable=False)

    # Reframing
    original_description = Column(Text, nullable=True)
    reframed_description = Column(Text, nullable=True)
    strengths_used = Column(Text, nullable=True)  # JSON array

    # Status
    completed = Column(Boolean, default=False, index=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    goal = relationship("GoalDB", back_populates="atomic_blocks")


class UserProfileDB(Base):
    """User profile and personality storage"""
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # Basic info
    display_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)

    # Personality (JSON)
    signature_strengths = Column(Text, nullable=True)  # JSON
    learning_style = Column(String(50), nullable=True)

    # Preferences
    preferences = Column(Text, nullable=True)  # JSON

    # Stats
    total_goals = Column(Integer, default=0)
    total_tasks_completed = Column(Integer, default=0)
    current_ari_score = Column(Float, nullable=True)


class ProgressTapestryDB(Base):
    """Progress tapestry entries"""
    __tablename__ = "progress_tapestry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entry_id = Column(String(36), unique=True, nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)

    # Win details
    win_description = Column(Text, nullable=False)
    win_type = Column(String(50), nullable=False)
    goal_id = Column(String(36), nullable=True)
    pride_level = Column(Float, nullable=False)

    # Context
    strengths_used = Column(Text, nullable=True)  # JSON array
    connected_to = Column(Text, nullable=True)  # JSON array of entry IDs

    __table_args__ = (
        Index('idx_user_timestamp', 'user_id', 'timestamp'),
    )


class MomentumHistoryDB(Base):
    """Momentum loop state history"""
    __tablename__ = "momentum_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    state = Column(String(50), nullable=False)
    goal_id = Column(String(36), nullable=True)

    __table_args__ = (
        Index('idx_user_timestamp', 'user_id', 'timestamp'),
    )


# ============================================================================
# Database Manager
# ============================================================================

class DatabaseManager:
    """Manages database connections and operations"""

    def __init__(
        self,
        database_url: str = "sqlite+aiosqlite:///./ai_pal.db",
        echo: bool = False,
        pool_size: int = 5,
        max_overflow: int = 10
    ):
        """
        Initialize database manager

        Args:
            database_url: SQLAlchemy database URL
                - SQLite: "sqlite+aiosqlite:///./ai_pal.db"
                - PostgreSQL: "postgresql+asyncpg://user:pass@localhost/ai_pal"
            echo: Echo SQL statements (for debugging)
            pool_size: Connection pool size
            max_overflow: Max overflow connections
        """
        self.database_url = database_url
        self.is_sqlite = "sqlite" in database_url.lower()

        # Create async engine
        if self.is_sqlite:
            # SQLite doesn't support connection pooling
            self.engine = create_async_engine(
                database_url,
                echo=echo,
                poolclass=NullPool
            )
        else:
            # PostgreSQL with connection pooling
            self.engine = create_async_engine(
                database_url,
                echo=echo,
                pool_size=pool_size,
                max_overflow=max_overflow,
                poolclass=QueuePool
            )

        # Create async session factory
        self.async_session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        logger.info(f"DatabaseManager initialized with {database_url}")

    async def create_tables(self):
        """Create all tables"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")

    async def drop_tables(self):
        """Drop all tables (use with caution!)"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.warning("Database tables dropped")

    async def close(self):
        """Close database connections"""
        await self.engine.dispose()
        logger.info("Database connections closed")

    def get_session(self) -> AsyncSession:
        """
        Get a new async session

        Usage:
            async with db_manager.get_session() as session:
                # Use session
                pass
        """
        return self.async_session_factory()


# ============================================================================
# Repository Pattern - Data Access Layer
# ============================================================================

class ARIRepository:
    """Repository for ARI snapshot operations"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    async def save_snapshot(self, snapshot_data: Dict[str, Any]) -> str:
        """Save ARI snapshot"""
        async with self.db.get_session() as session:
            snapshot = ARISnapshotDB(**snapshot_data)
            session.add(snapshot)
            await session.commit()
            return snapshot.snapshot_id

    async def get_snapshots_by_user(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get snapshots for a user"""
        from sqlalchemy import select

        async with self.db.get_session() as session:
            query = select(ARISnapshotDB).where(ARISnapshotDB.user_id == user_id)

            if start_date:
                query = query.where(ARISnapshotDB.timestamp >= start_date)
            if end_date:
                query = query.where(ARISnapshotDB.timestamp <= end_date)

            query = query.order_by(ARISnapshotDB.timestamp.desc())

            if limit:
                query = query.limit(limit)

            result = await session.execute(query)
            snapshots = result.scalars().all()

            return [self._snapshot_to_dict(s) for s in snapshots]

    async def get_latest_snapshot(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get latest snapshot for user"""
        from sqlalchemy import select

        async with self.db.get_session() as session:
            query = select(ARISnapshotDB).where(
                ARISnapshotDB.user_id == user_id
            ).order_by(ARISnapshotDB.timestamp.desc()).limit(1)

            result = await session.execute(query)
            snapshot = result.scalar_one_or_none()

            return self._snapshot_to_dict(snapshot) if snapshot else None

    def _snapshot_to_dict(self, snapshot: ARISnapshotDB) -> Dict[str, Any]:
        """Convert snapshot model to dict"""
        return {
            "snapshot_id": snapshot.snapshot_id,
            "user_id": snapshot.user_id,
            "timestamp": snapshot.timestamp,
            "decision_quality": snapshot.decision_quality,
            "skill_development": snapshot.skill_development,
            "ai_reliance": snapshot.ai_reliance,
            "bottleneck_resolution": snapshot.bottleneck_resolution,
            "user_confidence": snapshot.user_confidence,
            "engagement": snapshot.engagement,
            "autonomy_perception": snapshot.autonomy_perception,
            "autonomy_retention": snapshot.autonomy_retention,
            "delta_agency": snapshot.delta_agency,
            "task_description": snapshot.task_description,
            "task_complexity": snapshot.task_complexity
        }


class GoalRepository:
    """Repository for goal operations"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    async def save_goal(self, goal_data: Dict[str, Any]) -> str:
        """Save goal"""
        async with self.db.get_session() as session:
            goal = GoalDB(**goal_data)
            session.add(goal)
            await session.commit()
            return goal.goal_id

    async def get_active_goals(self, user_id: str) -> List[Dict[str, Any]]:
        """Get active goals for user"""
        from sqlalchemy import select

        async with self.db.get_session() as session:
            query = select(GoalDB).where(
                GoalDB.user_id == user_id,
                GoalDB.status == "active"
            ).order_by(GoalDB.created_at.desc())

            result = await session.execute(query)
            goals = result.scalars().all()

            return [self._goal_to_dict(g) for g in goals]

    async def update_goal_status(self, goal_id: str, status: str):
        """Update goal status"""
        from sqlalchemy import select, update

        async with self.db.get_session() as session:
            stmt = update(GoalDB).where(
                GoalDB.goal_id == goal_id
            ).values(
                status=status,
                completed_at=datetime.now() if status == "completed" else None
            )
            await session.execute(stmt)
            await session.commit()

    def _goal_to_dict(self, goal: GoalDB) -> Dict[str, Any]:
        """Convert goal model to dict"""
        return {
            "goal_id": goal.goal_id,
            "user_id": goal.user_id,
            "description": goal.description,
            "importance": goal.importance,
            "complexity_level": goal.complexity_level,
            "estimated_value": goal.estimated_value,
            "status": goal.status,
            "created_at": goal.created_at,
            "completed_at": goal.completed_at,
            "deadline": goal.deadline
        }


class UserProfileRepository:
    """Repository for user profile operations"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    async def save_profile(self, profile_data: Dict[str, Any]) -> str:
        """Save or update user profile"""
        from sqlalchemy import select

        async with self.db.get_session() as session:
            # Check if profile exists
            query = select(UserProfileDB).where(
                UserProfileDB.user_id == profile_data["user_id"]
            )
            result = await session.execute(query)
            existing = result.scalar_one_or_none()

            if existing:
                # Update
                for key, value in profile_data.items():
                    if key != "user_id":
                        setattr(existing, key, value)
                existing.updated_at = datetime.now()
            else:
                # Create
                profile = UserProfileDB(**profile_data)
                session.add(profile)

            await session.commit()
            return profile_data["user_id"]

    async def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile"""
        from sqlalchemy import select

        async with self.db.get_session() as session:
            query = select(UserProfileDB).where(UserProfileDB.user_id == user_id)
            result = await session.execute(query)
            profile = result.scalar_one_or_none()

            return self._profile_to_dict(profile) if profile else None

    def _profile_to_dict(self, profile: UserProfileDB) -> Dict[str, Any]:
        """Convert profile model to dict"""
        return {
            "user_id": profile.user_id,
            "display_name": profile.display_name,
            "email": profile.email,
            "signature_strengths": json.loads(profile.signature_strengths) if profile.signature_strengths else None,
            "learning_style": profile.learning_style,
            "preferences": json.loads(profile.preferences) if profile.preferences else {},
            "total_goals": profile.total_goals,
            "total_tasks_completed": profile.total_tasks_completed,
            "current_ari_score": profile.current_ari_score,
            "created_at": profile.created_at,
            "updated_at": profile.updated_at
        }
