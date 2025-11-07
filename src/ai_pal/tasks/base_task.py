"""
Base Task Class for Celery Tasks

Provides common functionality for all background tasks:
- Database persistence
- Retry logic with exponential backoff
- Error tracking and logging
- Task execution timing
"""

import time
import traceback
from typing import Any, Dict, Optional
from datetime import datetime
from uuid import uuid4

from celery import Task
from loguru import logger

from ai_pal.storage.database import DatabaseManager, BackgroundTaskRepository


class AIpalTask(Task):
    """Base task class for AI-Pal background tasks"""

    # Task configuration
    autoretry_for = (Exception,)
    max_retries = 3
    default_retry_delay = 60  # 1 minute

    # Database manager instance (set by task setup)
    db_manager: Optional[DatabaseManager] = None
    task_repo: Optional[BackgroundTaskRepository] = None

    def __call__(self, *args, **kwargs) -> Any:
        """
        Execute task with database tracking

        Args:
            *args: Task arguments
            **kwargs: Task keyword arguments

        Returns:
            Task result
        """
        task_id = self.request.id
        task_name = self.name
        task_type = self._get_task_type()

        logger.info(f"Starting task: {task_name} ({task_id})")

        start_time = time.time()

        try:
            # Run the actual task implementation
            result = self.run(*args, **kwargs)

            duration = time.time() - start_time

            logger.info(f"Task {task_name} ({task_id}) completed successfully in {duration:.2f}s")

            return result

        except Exception as exc:
            duration = time.time() - start_time

            logger.error(f"Task {task_name} ({task_id}) failed after {duration:.2f}s: {exc}")
            logger.error(traceback.format_exc())

            # Retry with exponential backoff
            retry_count = self.request.retries
            if retry_count < self.max_retries:
                retry_delay = self.default_retry_delay * (2 ** retry_count)
                logger.info(
                    f"Retrying task {task_name} ({task_id}) in {retry_delay}s "
                    f"(attempt {retry_count + 1}/{self.max_retries})"
                )
                raise self.retry(exc=exc, countdown=int(retry_delay))
            else:
                logger.error(f"Max retries exceeded for task {task_name} ({task_id})")
                raise

    def run(self, *args, **kwargs) -> Any:
        """
        Task implementation - override in subclass

        Args:
            *args: Task arguments
            **kwargs: Task keyword arguments

        Returns:
            Task result
        """
        raise NotImplementedError("Subclasses must implement run()")

    def _get_task_type(self) -> str:
        """
        Get task type from task name

        Returns:
            Task type string
        """
        # Extract task type from full task name
        # e.g., "ai_pal.tasks.ari_tasks.aggregate_snapshots" -> "ari_snapshot"
        task_name = self.name
        if "ari_tasks" in task_name:
            return "ari_snapshot"
        elif "ffe_tasks" in task_name:
            return "ffe_planning"
        elif "edm_tasks" in task_name:
            return "edm_analysis"
        elif "model_tasks" in task_name:
            return "model_training"
        elif "maintenance_tasks" in task_name:
            return "maintenance"
        else:
            return "unknown"

    @classmethod
    def setup_db(cls, db_manager: DatabaseManager):
        """
        Setup database manager for all tasks

        Args:
            db_manager: Database manager instance
        """
        cls.db_manager = db_manager
        cls.task_repo = BackgroundTaskRepository(db_manager)
        logger.info("Database manager configured for tasks")

    async def on_before_execution(
        self,
        task_id: str,
        task_name: str,
        args: tuple,
        kwargs: Dict[str, Any]
    ):
        """
        Hook called before task execution

        Args:
            task_id: Celery task ID
            task_name: Task name
            args: Task arguments
            kwargs: Task keyword arguments
        """
        if not self.task_repo:
            logger.warning("Task repository not configured")
            return

        try:
            # Create database record
            db_task_id = str(uuid4())

            await self.task_repo.create_task(
                task_id=db_task_id,
                task_name=task_name,
                task_type=self._get_task_type(),
                args={"args": args},
                kwargs=kwargs
            )

            logger.debug(f"Created database record for task {task_name}")

        except Exception as exc:
            logger.error(f"Error creating database record: {exc}")

    async def on_after_execution(
        self,
        task_id: str,
        result: Any,
        duration: float,
        success: bool,
        error: Optional[str] = None,
        error_traceback: Optional[str] = None
    ):
        """
        Hook called after task execution

        Args:
            task_id: Database task ID
            result: Task result
            duration: Execution duration in seconds
            success: Whether task succeeded
            error: Error message if failed
            error_traceback: Error traceback if failed
        """
        if not self.task_repo:
            logger.warning("Task repository not configured")
            return

        try:
            status = "completed" if success else "failed"

            await self.task_repo.record_task_result(
                task_id=task_id,
                result=result if success else None,
                error_message=error,
                error_traceback=error_traceback,
                duration_seconds=duration
            )

            await self.task_repo.update_task_status(
                task_id=task_id,
                status=status,
                completed_at=datetime.now()
            )

            logger.debug(f"Updated database record for task {task_id}: {status}")

        except Exception as exc:
            logger.error(f"Error updating database record: {exc}")


def create_task_class(
    name: str,
    task_type: str,
    bind: bool = True,
    max_retries: int = 3
) -> type:
    """
    Factory function to create a task class

    Args:
        name: Task name
        task_type: Task type for categorization
        bind: Whether task is bound (has access to self)
        max_retries: Maximum retry attempts

    Returns:
        Task class
    """

    class GeneratedTask(AIpalTask):
        __doc__ = f"{name} task"
        name = name
        bind = bind
        max_retries = max_retries

    return GeneratedTask
