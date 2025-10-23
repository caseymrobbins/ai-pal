"""
LoRA (Low-Rank Adaptation) Fine-Tuning Infrastructure

Enables personalized model adaptation through parameter-efficient fine-tuning:
- Collects training data from user interactions
- Prepares datasets for fine-tuning
- Manages LoRA training jobs
- Evaluates and deploys fine-tuned adapters

Uses LoRA to fine-tune local SLMs without full retraining.

Part of Phase 2: Advanced Monitoring & Self-Improvement
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

from loguru import logger


class FineTuningStatus(Enum):
    """Fine-tuning job status"""
    PENDING = "pending"  # Collecting data
    PREPARING = "preparing"  # Preparing dataset
    TRAINING = "training"  # Training in progress
    EVALUATING = "evaluating"  # Evaluating results
    COMPLETED = "completed"  # Successfully completed
    FAILED = "failed"  # Training failed
    DEPLOYED = "deployed"  # Deployed to production


@dataclass
class TrainingExample:
    """Single training example for fine-tuning"""
    example_id: str
    timestamp: datetime
    user_id: str

    # Input/Output pair
    input_text: str
    output_text: str
    task_type: str  # "completion", "instruction_following", etc.

    # Quality metrics
    quality_score: float  # 0-1 (from user feedback or automatic evaluation)
    feedback_source: str  # "explicit", "implicit", "synthetic"

    # Context
    session_id: str
    metadata: Dict = field(default_factory=dict)


@dataclass
class FineTuningConfig:
    """Configuration for fine-tuning job"""
    # Model settings
    base_model: str = "microsoft/phi-2"  # Default SLM
    lora_rank: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.1

    # Training settings
    learning_rate: float = 3e-4
    num_epochs: int = 3
    batch_size: int = 4
    gradient_accumulation_steps: int = 4
    max_seq_length: int = 512

    # Quality settings
    min_quality_score: float = 0.7  # Only use high-quality examples
    min_examples: int = 100  # Minimum examples before training
    max_examples: int = 10000  # Maximum examples per job

    # Validation
    validation_split: float = 0.1
    early_stopping_patience: int = 3

    # Safety
    enable_bias_detection: bool = True
    enable_safety_checks: bool = True
    max_training_time_hours: int = 24


@dataclass
class FineTuningJob:
    """Fine-tuning job"""
    job_id: str
    created_at: datetime
    user_id: str  # User for personalized model
    status: FineTuningStatus

    # Configuration
    config: FineTuningConfig

    # Data
    training_examples: List[str] = field(default_factory=list)  # Example IDs
    num_examples: int = 0

    # Training metrics
    training_loss: Optional[float] = None
    validation_loss: Optional[float] = None
    perplexity: Optional[float] = None

    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Output
    adapter_path: Optional[str] = None  # Path to trained LoRA adapter
    evaluation_metrics: Dict = field(default_factory=dict)

    # Status
    error_message: Optional[str] = None
    deployed: bool = False


class LoRAFineTuner:
    """
    LoRA Fine-Tuning Infrastructure

    Manages the complete fine-tuning lifecycle:
    1. Collect training examples from user interactions
    2. Filter and prepare high-quality dataset
    3. Launch fine-tuning job with LoRA
    4. Evaluate results
    5. Deploy adapter to production

    Enables personalized models without full retraining.
    """

    def __init__(
        self,
        storage_dir: Path,
        models_dir: Path,
        default_config: Optional[FineTuningConfig] = None
    ):
        """
        Initialize LoRA Fine-Tuner

        Args:
            storage_dir: Directory for training data and jobs
            models_dir: Directory for saving fine-tuned models
            default_config: Default fine-tuning configuration
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)

        self.default_config = default_config or FineTuningConfig()

        # In-memory storage
        self.training_examples: Dict[str, TrainingExample] = {}
        self.fine_tuning_jobs: Dict[str, FineTuningJob] = {}

        # User-specific examples
        self.user_examples: Dict[str, List[str]] = {}  # user_id -> example_ids

        # Load existing data
        self._load_training_examples()
        self._load_fine_tuning_jobs()

        logger.info(
            f"LoRA Fine-Tuner initialized with storage at {storage_dir}, "
            f"models at {models_dir}"
        )

    def _load_training_examples(self) -> None:
        """Load existing training examples"""
        examples_dir = self.storage_dir / "examples"
        if not examples_dir.exists():
            return

        for example_file in examples_dir.glob("*.json"):
            try:
                with open(example_file, 'r') as f:
                    data = json.load(f)
                    example = TrainingExample(
                        example_id=data["example_id"],
                        timestamp=datetime.fromisoformat(data["timestamp"]),
                        user_id=data["user_id"],
                        input_text=data["input_text"],
                        output_text=data["output_text"],
                        task_type=data["task_type"],
                        quality_score=data["quality_score"],
                        feedback_source=data["feedback_source"],
                        session_id=data["session_id"],
                        metadata=data.get("metadata", {})
                    )

                    self.training_examples[example.example_id] = example

                    # Track by user
                    if example.user_id not in self.user_examples:
                        self.user_examples[example.user_id] = []
                    self.user_examples[example.user_id].append(example.example_id)

            except Exception as e:
                logger.error(f"Failed to load training example {example_file}: {e}")

    def _load_fine_tuning_jobs(self) -> None:
        """Load existing fine-tuning jobs"""
        jobs_dir = self.storage_dir / "jobs"
        if not jobs_dir.exists():
            return

        for job_file in jobs_dir.glob("*.json"):
            try:
                with open(job_file, 'r') as f:
                    data = json.load(f)

                    # Reconstruct config
                    config_data = data["config"]
                    config = FineTuningConfig(
                        base_model=config_data.get("base_model", "microsoft/phi-2"),
                        lora_rank=config_data.get("lora_rank", 8),
                        lora_alpha=config_data.get("lora_alpha", 16),
                        lora_dropout=config_data.get("lora_dropout", 0.1),
                        learning_rate=config_data.get("learning_rate", 3e-4),
                        num_epochs=config_data.get("num_epochs", 3),
                        batch_size=config_data.get("batch_size", 4),
                        gradient_accumulation_steps=config_data.get("gradient_accumulation_steps", 4),
                        max_seq_length=config_data.get("max_seq_length", 512),
                        min_quality_score=config_data.get("min_quality_score", 0.7),
                        min_examples=config_data.get("min_examples", 100),
                        max_examples=config_data.get("max_examples", 10000),
                        validation_split=config_data.get("validation_split", 0.1),
                        early_stopping_patience=config_data.get("early_stopping_patience", 3),
                        enable_bias_detection=config_data.get("enable_bias_detection", True),
                        enable_safety_checks=config_data.get("enable_safety_checks", True),
                        max_training_time_hours=config_data.get("max_training_time_hours", 24)
                    )

                    job = FineTuningJob(
                        job_id=data["job_id"],
                        created_at=datetime.fromisoformat(data["created_at"]),
                        user_id=data["user_id"],
                        status=FineTuningStatus(data["status"]),
                        config=config,
                        training_examples=data.get("training_examples", []),
                        num_examples=data.get("num_examples", 0),
                        training_loss=data.get("training_loss"),
                        validation_loss=data.get("validation_loss"),
                        perplexity=data.get("perplexity"),
                        started_at=datetime.fromisoformat(data["started_at"])
                        if data.get("started_at") else None,
                        completed_at=datetime.fromisoformat(data["completed_at"])
                        if data.get("completed_at") else None,
                        adapter_path=data.get("adapter_path"),
                        evaluation_metrics=data.get("evaluation_metrics", {}),
                        error_message=data.get("error_message"),
                        deployed=data.get("deployed", False)
                    )

                    self.fine_tuning_jobs[job.job_id] = job

            except Exception as e:
                logger.error(f"Failed to load fine-tuning job {job_file}: {e}")

    async def collect_training_example(
        self,
        user_id: str,
        input_text: str,
        output_text: str,
        task_type: str,
        quality_score: float,
        feedback_source: str,
        session_id: str,
        metadata: Optional[Dict] = None
    ) -> TrainingExample:
        """
        Collect a training example from user interaction

        Args:
            user_id: User ID
            input_text: Input/prompt
            output_text: Output/completion
            task_type: Type of task
            quality_score: Quality score (0-1)
            feedback_source: Source of quality score
            session_id: Session ID
            metadata: Additional metadata

        Returns:
            Created training example
        """
        example_id = f"{user_id}_{datetime.now().timestamp()}"

        example = TrainingExample(
            example_id=example_id,
            timestamp=datetime.now(),
            user_id=user_id,
            input_text=input_text,
            output_text=output_text,
            task_type=task_type,
            quality_score=quality_score,
            feedback_source=feedback_source,
            session_id=session_id,
            metadata=metadata or {}
        )

        # Store in memory
        self.training_examples[example_id] = example

        if user_id not in self.user_examples:
            self.user_examples[user_id] = []
        self.user_examples[user_id].append(example_id)

        # Persist to disk
        await self._persist_training_example(example)

        logger.debug(
            f"Collected training example for user {user_id}, "
            f"quality: {quality_score:.2f}"
        )

        # Check if user has enough examples for fine-tuning
        await self._check_fine_tuning_threshold(user_id)

        return example

    async def _persist_training_example(self, example: TrainingExample) -> None:
        """Persist training example to disk"""
        examples_dir = self.storage_dir / "examples"
        examples_dir.mkdir(exist_ok=True)

        filepath = examples_dir / f"{example.example_id}.json"

        try:
            with open(filepath, 'w') as f:
                json.dump({
                    "example_id": example.example_id,
                    "timestamp": example.timestamp.isoformat(),
                    "user_id": example.user_id,
                    "input_text": example.input_text,
                    "output_text": example.output_text,
                    "task_type": example.task_type,
                    "quality_score": example.quality_score,
                    "feedback_source": example.feedback_source,
                    "session_id": example.session_id,
                    "metadata": example.metadata
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist training example: {e}")

    async def _check_fine_tuning_threshold(self, user_id: str) -> None:
        """Check if user has enough examples to trigger fine-tuning"""
        if user_id not in self.user_examples:
            return

        # Get high-quality examples
        high_quality_examples = [
            example_id for example_id in self.user_examples[user_id]
            if self.training_examples[example_id].quality_score >= self.default_config.min_quality_score
        ]

        if len(high_quality_examples) >= self.default_config.min_examples:
            logger.info(
                f"User {user_id} has {len(high_quality_examples)} high-quality examples, "
                f"eligible for fine-tuning"
            )

            # Optionally auto-create fine-tuning job
            # For now, just log it

    async def create_fine_tuning_job(
        self,
        user_id: str,
        config: Optional[FineTuningConfig] = None
    ) -> FineTuningJob:
        """
        Create a new fine-tuning job for a user

        Args:
            user_id: User to create personalized model for
            config: Fine-tuning configuration (uses default if not provided)

        Returns:
            Created fine-tuning job
        """
        job_id = f"ft_{user_id}_{datetime.now().timestamp()}"

        config = config or self.default_config

        # Get user's high-quality examples
        if user_id not in self.user_examples:
            raise ValueError(f"No training examples found for user {user_id}")

        high_quality_examples = [
            example_id for example_id in self.user_examples[user_id]
            if self.training_examples[example_id].quality_score >= config.min_quality_score
        ]

        if len(high_quality_examples) < config.min_examples:
            raise ValueError(
                f"Insufficient high-quality examples: {len(high_quality_examples)} "
                f"(minimum: {config.min_examples})"
            )

        # Limit to max examples
        if len(high_quality_examples) > config.max_examples:
            # Take most recent examples
            sorted_examples = sorted(
                high_quality_examples,
                key=lambda eid: self.training_examples[eid].timestamp,
                reverse=True
            )
            high_quality_examples = sorted_examples[:config.max_examples]

        job = FineTuningJob(
            job_id=job_id,
            created_at=datetime.now(),
            user_id=user_id,
            status=FineTuningStatus.PENDING,
            config=config,
            training_examples=high_quality_examples,
            num_examples=len(high_quality_examples)
        )

        self.fine_tuning_jobs[job_id] = job
        await self._persist_fine_tuning_job(job)

        logger.info(
            f"Created fine-tuning job {job_id} for user {user_id} "
            f"with {len(high_quality_examples)} examples"
        )

        return job

    async def _persist_fine_tuning_job(self, job: FineTuningJob) -> None:
        """Persist fine-tuning job to disk"""
        jobs_dir = self.storage_dir / "jobs"
        jobs_dir.mkdir(exist_ok=True)

        filepath = jobs_dir / f"{job.job_id}.json"

        try:
            config_dict = {
                "base_model": job.config.base_model,
                "lora_rank": job.config.lora_rank,
                "lora_alpha": job.config.lora_alpha,
                "lora_dropout": job.config.lora_dropout,
                "learning_rate": job.config.learning_rate,
                "num_epochs": job.config.num_epochs,
                "batch_size": job.config.batch_size,
                "gradient_accumulation_steps": job.config.gradient_accumulation_steps,
                "max_seq_length": job.config.max_seq_length,
                "min_quality_score": job.config.min_quality_score,
                "min_examples": job.config.min_examples,
                "max_examples": job.config.max_examples,
                "validation_split": job.config.validation_split,
                "early_stopping_patience": job.config.early_stopping_patience,
                "enable_bias_detection": job.config.enable_bias_detection,
                "enable_safety_checks": job.config.enable_safety_checks,
                "max_training_time_hours": job.config.max_training_time_hours
            }

            with open(filepath, 'w') as f:
                json.dump({
                    "job_id": job.job_id,
                    "created_at": job.created_at.isoformat(),
                    "user_id": job.user_id,
                    "status": job.status.value,
                    "config": config_dict,
                    "training_examples": job.training_examples,
                    "num_examples": job.num_examples,
                    "training_loss": job.training_loss,
                    "validation_loss": job.validation_loss,
                    "perplexity": job.perplexity,
                    "started_at": job.started_at.isoformat() if job.started_at else None,
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                    "adapter_path": job.adapter_path,
                    "evaluation_metrics": job.evaluation_metrics,
                    "error_message": job.error_message,
                    "deployed": job.deployed
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist fine-tuning job: {e}")

    async def start_fine_tuning(self, job_id: str) -> bool:
        """
        Start fine-tuning job

        In production, this would:
        1. Prepare dataset in correct format
        2. Initialize LoRA-wrapped model
        3. Launch training with proper hyperparameters
        4. Monitor progress and save checkpoints
        5. Evaluate on validation set
        6. Save final adapter

        For now, this is a placeholder that simulates the process.

        Args:
            job_id: Job ID to start

        Returns:
            True if started successfully
        """
        if job_id not in self.fine_tuning_jobs:
            logger.error(f"Job {job_id} not found")
            return False

        job = self.fine_tuning_jobs[job_id]

        if job.status != FineTuningStatus.PENDING:
            logger.warning(f"Job {job_id} is not in PENDING status")
            return False

        # Update status
        job.status = FineTuningStatus.PREPARING
        job.started_at = datetime.now()
        await self._persist_fine_tuning_job(job)

        logger.info(f"Starting fine-tuning job {job_id}")

        # In production, this would:
        # 1. Use transformers + PEFT to add LoRA adapters
        # 2. Prepare datasets using training examples
        # 3. Train with specified hyperparameters
        # 4. Save adapter weights

        # Simulate training (placeholder)
        asyncio.create_task(self._simulate_training(job))

        return True

    async def _simulate_training(self, job: FineTuningJob) -> None:
        """Simulate training process (placeholder for actual implementation)"""
        try:
            # Simulate preparing dataset
            await asyncio.sleep(2)
            job.status = FineTuningStatus.TRAINING
            await self._persist_fine_tuning_job(job)

            # Simulate training
            await asyncio.sleep(5)

            # Simulate results
            job.training_loss = 0.45
            job.validation_loss = 0.52
            job.perplexity = 1.68
            job.adapter_path = str(self.models_dir / job.job_id / "adapter_model.bin")
            job.evaluation_metrics = {
                "accuracy": 0.87,
                "f1_score": 0.85,
                "perplexity": 1.68
            }

            job.status = FineTuningStatus.COMPLETED
            job.completed_at = datetime.now()
            await self._persist_fine_tuning_job(job)

            logger.info(f"Fine-tuning job {job.job_id} completed successfully")

        except Exception as e:
            job.status = FineTuningStatus.FAILED
            job.error_message = str(e)
            await self._persist_fine_tuning_job(job)
            logger.error(f"Fine-tuning job {job.job_id} failed: {e}")

    async def deploy_adapter(self, job_id: str) -> bool:
        """
        Deploy fine-tuned adapter to production

        Args:
            job_id: Job ID with completed fine-tuning

        Returns:
            True if deployed successfully
        """
        if job_id not in self.fine_tuning_jobs:
            logger.error(f"Job {job_id} not found")
            return False

        job = self.fine_tuning_jobs[job_id]

        if job.status != FineTuningStatus.COMPLETED:
            logger.error(f"Job {job_id} is not completed")
            return False

        # In production, this would load the adapter and make it available
        job.status = FineTuningStatus.DEPLOYED
        job.deployed = True
        await self._persist_fine_tuning_job(job)

        logger.info(f"Deployed LoRA adapter for job {job_id}")
        return True

    def get_user_stats(self, user_id: str) -> Dict:
        """Get statistics for a user"""
        if user_id not in self.user_examples:
            return {
                "user_id": user_id,
                "total_examples": 0,
                "high_quality_examples": 0,
                "fine_tuning_jobs": 0
            }

        examples = [self.training_examples[eid] for eid in self.user_examples[user_id]]
        high_quality = [
            e for e in examples
            if e.quality_score >= self.default_config.min_quality_score
        ]

        jobs = [
            j for j in self.fine_tuning_jobs.values()
            if j.user_id == user_id
        ]

        return {
            "user_id": user_id,
            "total_examples": len(examples),
            "high_quality_examples": len(high_quality),
            "average_quality": sum(e.quality_score for e in examples) / len(examples),
            "fine_tuning_jobs": len(jobs),
            "deployed_adapters": sum(1 for j in jobs if j.deployed)
        }
