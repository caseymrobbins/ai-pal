"""
Background Job Processing - Async Task Queue

Provides async task execution for:
- ARI snapshot batch processing
- EDM debt analysis
- Goal progress calculations
- Dashboard data aggregation
- Cache warming
- Data cleanup and archival

Features:
- Asyncio-based task queue
- Priority levels
- Retry logic with exponential backoff
- Task scheduling (cron-like)
- Graceful shutdown
- Task monitoring and stats
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
import traceback
from collections import defaultdict

from loguru import logger


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class TaskResult:
    """Result of a task execution"""
    task_id: str
    status: TaskStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    attempts: int = 0


@dataclass
class BackgroundTask:
    """Background task definition"""
    task_id: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    max_retries: int = 3
    retry_delay: float = 1.0  # Initial delay in seconds
    timeout: Optional[float] = None  # Timeout in seconds

    # Internal state
    attempts: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    result: Optional[TaskResult] = None


class TaskQueue:
    """
    Async task queue with priority and retry support

    Usage:
        queue = TaskQueue(max_workers=5)
        await queue.start()

        # Submit task
        task_id = await queue.submit(
            my_async_function,
            arg1, arg2,
            priority=TaskPriority.HIGH,
            max_retries=3
        )

        # Wait for result
        result = await queue.get_result(task_id)

        # Shutdown
        await queue.shutdown()
    """

    def __init__(self, max_workers: int = 5):
        """
        Initialize task queue

        Args:
            max_workers: Maximum concurrent workers
        """
        self.max_workers = max_workers
        self.tasks: Dict[str, BackgroundTask] = {}
        self.pending_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.workers: List[asyncio.Task] = []
        self.running = False
        self.stats = defaultdict(int)

        logger.info(f"TaskQueue initialized with {max_workers} workers")

    async def start(self):
        """Start task queue workers"""
        if self.running:
            logger.warning("TaskQueue already running")
            return

        self.running = True

        # Create worker tasks
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(i))
            self.workers.append(worker)

        logger.info(f"TaskQueue started with {self.max_workers} workers")

    async def shutdown(self, wait: bool = True):
        """
        Shutdown task queue

        Args:
            wait: Wait for pending tasks to complete
        """
        self.running = False

        if wait:
            # Wait for pending tasks
            await self.pending_queue.join()

        # Cancel workers
        for worker in self.workers:
            worker.cancel()

        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)

        self.workers = []
        logger.info("TaskQueue shut down")

    async def submit(
        self,
        func: Callable,
        *args,
        priority: TaskPriority = TaskPriority.NORMAL,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        Submit a task to the queue

        Args:
            func: Async function to execute
            *args: Positional arguments
            priority: Task priority
            max_retries: Maximum retry attempts
            retry_delay: Initial retry delay (doubles each retry)
            timeout: Task timeout in seconds
            **kwargs: Keyword arguments

        Returns:
            Task ID
        """
        # Generate task ID
        task_id = f"task_{datetime.now().timestamp()}_{len(self.tasks)}"

        # Create task
        task = BackgroundTask(
            task_id=task_id,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout
        )

        # Store task
        self.tasks[task_id] = task

        # Queue task (priority queue uses negative priority for highest first)
        await self.pending_queue.put((-priority.value, task_id))

        self.stats["submitted"] += 1
        logger.debug(f"Task {task_id} submitted with priority {priority.name}")

        return task_id

    async def get_result(
        self,
        task_id: str,
        timeout: Optional[float] = None
    ) -> Optional[TaskResult]:
        """
        Get task result (blocks until complete)

        Args:
            task_id: Task ID
            timeout: Wait timeout in seconds

        Returns:
            TaskResult or None if timeout
        """
        task = self.tasks.get(task_id)
        if not task:
            return None

        # Wait for result with optional timeout
        start = datetime.now()
        while task.result is None or task.result.status in [TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.RETRYING]:
            if timeout and (datetime.now() - start).total_seconds() > timeout:
                return None
            await asyncio.sleep(0.1)

        return task.result

    async def get_pending_count(self) -> int:
        """Get number of pending tasks"""
        return self.pending_queue.qsize()

    async def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        return {
            "submitted": self.stats["submitted"],
            "completed": self.stats["completed"],
            "failed": self.stats["failed"],
            "retried": self.stats["retried"],
            "pending": self.pending_queue.qsize(),
            "workers": len(self.workers),
            "running": self.running
        }

    async def _worker(self, worker_id: int):
        """
        Worker coroutine

        Args:
            worker_id: Worker ID
        """
        logger.info(f"Worker {worker_id} started")

        while self.running:
            try:
                # Get next task (with timeout to check running flag)
                try:
                    _, task_id = await asyncio.wait_for(
                        self.pending_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                # Execute task
                await self._execute_task(worker_id, task_id)

                # Mark queue task as done
                self.pending_queue.task_done()

            except asyncio.CancelledError:
                logger.info(f"Worker {worker_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                logger.error(traceback.format_exc())

        logger.info(f"Worker {worker_id} stopped")

    async def _execute_task(self, worker_id: int, task_id: str):
        """
        Execute a task

        Args:
            worker_id: Worker ID
            task_id: Task ID
        """
        task = self.tasks.get(task_id)
        if not task:
            logger.warning(f"Task {task_id} not found")
            return

        task.attempts += 1
        started_at = datetime.now()

        # Create result
        result = TaskResult(
            task_id=task_id,
            status=TaskStatus.RUNNING,
            started_at=started_at,
            attempts=task.attempts
        )
        task.result = result

        logger.debug(f"Worker {worker_id} executing task {task_id} (attempt {task.attempts}/{task.max_retries + 1})")

        try:
            # Execute with optional timeout
            if task.timeout:
                task_result = await asyncio.wait_for(
                    task.func(*task.args, **task.kwargs),
                    timeout=task.timeout
                )
            else:
                task_result = await task.func(*task.args, **task.kwargs)

            # Success
            result.status = TaskStatus.COMPLETED
            result.result = task_result
            result.completed_at = datetime.now()

            self.stats["completed"] += 1
            logger.debug(f"Task {task_id} completed successfully")

        except asyncio.TimeoutError:
            # Timeout
            error_msg = f"Task timed out after {task.timeout}s"
            logger.warning(f"Task {task_id}: {error_msg}")

            if task.attempts < task.max_retries + 1:
                # Retry
                await self._retry_task(task)
            else:
                # Max retries exceeded
                result.status = TaskStatus.FAILED
                result.error = error_msg
                result.completed_at = datetime.now()
                self.stats["failed"] += 1

        except Exception as e:
            # Error
            error_msg = f"{type(e).__name__}: {str(e)}"
            logger.error(f"Task {task_id} failed: {error_msg}")
            logger.error(traceback.format_exc())

            if task.attempts < task.max_retries + 1:
                # Retry
                await self._retry_task(task)
            else:
                # Max retries exceeded
                result.status = TaskStatus.FAILED
                result.error = error_msg
                result.completed_at = datetime.now()
                self.stats["failed"] += 1

    async def _retry_task(self, task: BackgroundTask):
        """
        Retry a failed task

        Args:
            task: Task to retry
        """
        # Update status
        if task.result:
            task.result.status = TaskStatus.RETRYING

        # Calculate backoff delay (exponential)
        delay = task.retry_delay * (2 ** (task.attempts - 1))

        logger.info(f"Retrying task {task.task_id} in {delay:.1f}s (attempt {task.attempts + 1}/{task.max_retries + 1})")

        self.stats["retried"] += 1

        # Schedule retry
        await asyncio.sleep(delay)
        await self.pending_queue.put((-task.priority.value, task.task_id))


# ============================================================================
# Scheduled Tasks
# ============================================================================

class ScheduledTask:
    """Scheduled task definition"""

    def __init__(
        self,
        name: str,
        func: Callable,
        interval: timedelta,
        args: tuple = (),
        kwargs: dict = None,
        start_immediately: bool = False
    ):
        """
        Initialize scheduled task

        Args:
            name: Task name
            func: Async function to execute
            interval: Execution interval
            args: Positional arguments
            kwargs: Keyword arguments
            start_immediately: Run immediately on start
        """
        self.name = name
        self.func = func
        self.interval = interval
        self.args = args
        self.kwargs = kwargs or {}
        self.start_immediately = start_immediately

        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = None
        self.run_count: int = 0
        self.error_count: int = 0


class TaskScheduler:
    """
    Task scheduler for periodic execution

    Usage:
        scheduler = TaskScheduler()

        # Add scheduled task
        scheduler.add_task(
            "cleanup",
            cleanup_old_data,
            interval=timedelta(hours=24)
        )

        # Start scheduler
        await scheduler.start()

        # Stop scheduler
        await scheduler.stop()
    """

    def __init__(self):
        """Initialize task scheduler"""
        self.tasks: Dict[str, ScheduledTask] = {}
        self.running = False
        self.scheduler_task: Optional[asyncio.Task] = None

        logger.info("TaskScheduler initialized")

    def add_task(
        self,
        name: str,
        func: Callable,
        interval: timedelta,
        args: tuple = (),
        kwargs: dict = None,
        start_immediately: bool = False
    ):
        """
        Add a scheduled task

        Args:
            name: Task name (must be unique)
            func: Async function to execute
            interval: Execution interval
            args: Positional arguments
            kwargs: Keyword arguments
            start_immediately: Run immediately on start
        """
        task = ScheduledTask(
            name=name,
            func=func,
            interval=interval,
            args=args,
            kwargs=kwargs,
            start_immediately=start_immediately
        )

        self.tasks[name] = task
        logger.info(f"Scheduled task '{name}' added (interval: {interval})")

    def remove_task(self, name: str):
        """Remove a scheduled task"""
        if name in self.tasks:
            del self.tasks[name]
            logger.info(f"Scheduled task '{name}' removed")

    async def start(self):
        """Start task scheduler"""
        if self.running:
            logger.warning("TaskScheduler already running")
            return

        self.running = True
        self.scheduler_task = asyncio.create_task(self._run_scheduler())
        logger.info("TaskScheduler started")

    async def stop(self):
        """Stop task scheduler"""
        self.running = False
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        logger.info("TaskScheduler stopped")

    async def _run_scheduler(self):
        """Main scheduler loop"""
        # Initialize next_run times
        now = datetime.now()
        for task in self.tasks.values():
            if task.start_immediately:
                task.next_run = now
            else:
                task.next_run = now + task.interval

        while self.running:
            try:
                now = datetime.now()

                # Check each task
                for task in self.tasks.values():
                    if task.next_run and now >= task.next_run:
                        # Execute task
                        asyncio.create_task(self._execute_scheduled_task(task))

                        # Schedule next run
                        task.next_run = now + task.interval

                # Sleep for a bit
                await asyncio.sleep(1.0)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                logger.error(traceback.format_exc())
                await asyncio.sleep(5.0)

    async def _execute_scheduled_task(self, task: ScheduledTask):
        """Execute a scheduled task"""
        logger.debug(f"Executing scheduled task '{task.name}'")

        try:
            await task.func(*task.args, **task.kwargs)

            task.last_run = datetime.now()
            task.run_count += 1

            logger.debug(f"Scheduled task '{task.name}' completed (run #{task.run_count})")

        except Exception as e:
            task.error_count += 1
            logger.error(f"Scheduled task '{task.name}' failed: {e}")
            logger.error(traceback.format_exc())
