#!/usr/bin/env python3
"""
PostgreSQL Migration Script

Handles database optimization, index creation, and performance tuning for PostgreSQL.
Run this script after setting up PostgreSQL to optimize the schema.

Usage:
    python scripts/postgres_migration.py --optimize
    python scripts/postgres_migration.py --create-indexes
    python scripts/postgres_migration.py --analyze
"""

import asyncio
import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import text
from ai_pal.storage.database import DatabaseManager
from ai_pal.monitoring import get_logger

logger = get_logger("postgres_migration")


class PostgreSQLOptimizer:
    """Handles PostgreSQL schema optimization and migrations"""

    def __init__(self, database_url: str):
        """Initialize with database URL"""
        self.db = DatabaseManager(database_url)

    async def create_indexes(self):
        """Create all performance indexes"""
        logger.info("Creating database indexes...")

        indexes = [
            # ARI Snapshots
            ("idx_ari_user_id", "ari_snapshots", ["user_id"]),
            ("idx_ari_timestamp", "ari_snapshots", ["created_at DESC"]),
            ("idx_ari_user_timestamp", "ari_snapshots", ["user_id", "timestamp DESC"]),
            ("idx_ari_score", "ari_snapshots", ["autonomy_retention DESC"]),

            # EDM Debts
            ("idx_edm_user_id", "edm_debts", ["user_id"]),
            ("idx_edm_severity", "edm_debts", ["severity"]),
            ("idx_edm_resolved", "edm_debts", ["resolved"]),
            ("idx_edm_user_unresolved", "edm_debts", ["user_id", "resolved"]),

            # FFE Goals
            ("idx_goal_user_id", "ffe_goals", ["user_id"]),
            ("idx_goal_status", "ffe_goals", ["status"]),
            ("idx_goal_deadline", "ffe_goals", ["deadline"]),
            ("idx_goal_user_status", "ffe_goals", ["user_id", "status"]),

            # Background Tasks
            ("idx_task_id", "background_tasks", ["task_id"]),
            ("idx_task_user_id", "background_tasks", ["user_id"]),
            ("idx_task_status", "background_tasks", ["status"]),
            ("idx_task_type", "background_tasks", ["task_type"]),
            ("idx_task_created", "background_tasks", ["created_at DESC"]),
            ("idx_task_user_status", "background_tasks", ["user_id", "status"]),
            ("idx_task_celery_id", "background_tasks", ["celery_task_id"]),

            # Atomic Blocks
            ("idx_block_goal_id", "atomic_blocks", ["goal_id"]),
            ("idx_block_user_id", "atomic_blocks", ["user_id"]),

            # Audit Logs
            ("idx_audit_user_timestamp", "audit_logs", ["user_id", "timestamp DESC"]),
            ("idx_audit_severity", "audit_logs", ["severity"]),

            # Patches
            ("idx_patch_status", "ai_patches", ["status"]),
            ("idx_patch_component_status", "ai_patches", ["component", "status"]),

            # Appeals
            ("idx_appeal_status", "appeals", ["status"]),
        ]

        async with self.db.get_session() as session:
            for index_name, table, columns in indexes:
                try:
                    column_str = ", ".join(columns)
                    create_index_sql = f"""
                        CREATE INDEX IF NOT EXISTS {index_name}
                        ON {table} ({column_str})
                    """
                    await session.execute(text(create_index_sql))
                    logger.info(f"✓ Created index: {index_name}")
                except Exception as e:
                    logger.warning(f"⚠ Could not create index {index_name}: {e}")

            await session.commit()

    async def add_constraints(self):
        """Add foreign key and uniqueness constraints"""
        logger.info("Adding database constraints...")

        constraints = [
            # Foreign keys
            ("ALTER TABLE atomic_blocks ADD CONSTRAINT fk_block_goal_id "
             "FOREIGN KEY (goal_id) REFERENCES ffe_goals(goal_id) ON DELETE CASCADE"),

            # Unique constraints already in models, but ensure they're created
        ]

        async with self.db.get_session() as session:
            for constraint_sql in constraints:
                try:
                    await session.execute(text(constraint_sql))
                    logger.info(f"✓ Added constraint")
                except Exception as e:
                    logger.warning(f"⚠ Could not add constraint: {e}")

            await session.commit()

    async def analyze_tables(self):
        """Analyze tables for query optimization"""
        logger.info("Analyzing tables for query optimization...")

        tables = [
            "ari_snapshots",
            "edm_debts",
            "ffe_goals",
            "atomic_blocks",
            "background_tasks",
            "audit_logs",
            "ai_patches",
            "appeals",
        ]

        async with self.db.get_session() as session:
            for table in tables:
                try:
                    await session.execute(text(f"ANALYZE {table}"))
                    logger.info(f"✓ Analyzed table: {table}")
                except Exception as e:
                    logger.warning(f"⚠ Could not analyze {table}: {e}")

            await session.commit()

    async def get_table_stats(self):
        """Get table statistics"""
        logger.info("Gathering table statistics...")

        async with self.db.get_session() as session:
            result = await session.execute(text("""
                SELECT
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
                    n_live_tup AS row_count
                FROM pg_stat_user_tables
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            """))

            logger.info("\n=== Table Statistics ===")
            for row in result:
                logger.info(f"{row[1]}: {row[2]} ({row[3]:,} rows)")

    async def run_full_optimization(self):
        """Run full optimization suite"""
        logger.info("Starting PostgreSQL optimization suite...")

        try:
            await self.db.create_tables()
            logger.info("✓ Tables created/verified")

            await self.add_constraints()
            await self.create_indexes()
            await self.analyze_tables()
            await self.get_table_stats()

            logger.info("✓ PostgreSQL optimization complete!")

        finally:
            await self.db.close()


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="PostgreSQL Migration and Optimization Tool"
    )
    parser.add_argument(
        "--database-url",
        default="postgresql+asyncpg://ai_pal_user:aipal_secure_password_123@localhost:5432/ai_pal",
        help="Database URL"
    )
    parser.add_argument(
        "--optimize",
        action="store_true",
        help="Run full optimization"
    )
    parser.add_argument(
        "--create-indexes",
        action="store_true",
        help="Create indexes only"
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Analyze tables only"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show table statistics"
    )

    args = parser.parse_args()

    optimizer = PostgreSQLOptimizer(args.database_url)

    try:
        if args.optimize:
            await optimizer.run_full_optimization()
        elif args.create_indexes:
            await optimizer.create_indexes()
            await optimizer.db.close()
        elif args.analyze:
            await optimizer.analyze_tables()
            await optimizer.get_table_stats()
            await optimizer.db.close()
        elif args.stats:
            await optimizer.get_table_stats()
            await optimizer.db.close()
        else:
            parser.print_help()
    except Exception as e:
        logger.error(f"Error during optimization: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
