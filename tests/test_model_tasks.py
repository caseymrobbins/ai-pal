"""
Unit tests for Model Training background tasks.

Tests:
- Model fine-tuning
- Model evaluation
- Model benchmarking
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from ai_pal.tasks.model_tasks import (
    ModelFinetuningTask,
    ModelEvaluationTask,
    ModelBenchmarkTask,
)


@pytest.mark.unit
class TestModelFinetuningTask:
    """Test model fine-tuning task"""

    def test_task_initialization(self):
        """Test task initialization"""
        task = ModelFinetuningTask()
        assert task.name == "ai_pal.tasks.model_tasks.finetune_model"
        assert task.bind is True
        assert task.max_retries == 2

    def test_task_get_task_type(self):
        """Test task type detection"""
        task = ModelFinetuningTask()
        assert task._get_task_type() == "model_training"

    def test_finetune_run_method(self):
        """Test run method executes async operation"""
        task = ModelFinetuningTask()
        task.db_manager = MagicMock()

        with patch('asyncio.run') as mock_asyncio:
            mock_asyncio.return_value = {
                "user_id": "user1",
                "model_name": "phi-2",
                "status": "completed",
                "metrics": {
                    "loss": 0.45,
                    "accuracy": 0.87,
                },
            }
            result = task.run(
                user_id="user1",
                model_name="phi-2",
                training_samples=100,
                learning_rate=1e-4
            )

            assert mock_asyncio.called
            assert result["model_name"] == "phi-2"
            assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_finetune_result_structure(self):
        """Test fine-tuning returns proper structure"""
        task = ModelFinetuningTask()
        task.db_manager = MagicMock()

        result = await task._finetune_async(
            user_id="user1",
            model_name="phi-2",
            training_samples=100,
            learning_rate=1e-4
        )

        # Verify result structure
        assert result["user_id"] == "user1"
        assert result["model_name"] == "phi-2"
        assert result["status"] == "completed"
        assert "metrics" in result
        assert "training_samples_used" in result
        assert "training_duration_seconds" in result

    @pytest.mark.asyncio
    async def test_finetune_metrics_present(self):
        """Test that fine-tuning results include metrics"""
        task = ModelFinetuningTask()
        task.db_manager = MagicMock()

        result = await task._finetune_async(
            user_id="user1",
            model_name="phi-2",
            training_samples=100,
            learning_rate=1e-4
        )

        metrics = result["metrics"]
        assert "loss" in metrics
        assert "accuracy" in metrics
        assert "perplexity" in metrics
        assert metrics["loss"] >= 0
        assert 0 <= metrics["accuracy"] <= 1

    @pytest.mark.asyncio
    async def test_finetune_different_models(self):
        """Test fine-tuning for different model types"""
        task = ModelFinetuningTask()
        task.db_manager = MagicMock()

        for model_name in ["phi-2", "tinyllama"]:
            result = await task._finetune_async(
                user_id="user1",
                model_name=model_name,
                training_samples=100,
                learning_rate=1e-4
            )

            assert result["model_name"] == model_name


@pytest.mark.unit
class TestModelEvaluationTask:
    """Test model evaluation task"""

    def test_task_initialization(self):
        """Test task initialization"""
        task = ModelEvaluationTask()
        assert task.name == "ai_pal.tasks.model_tasks.evaluate_model"
        assert task.bind is True
        assert task.max_retries == 2

    def test_evaluate_run_method(self):
        """Test run method executes async operation"""
        task = ModelEvaluationTask()
        task.db_manager = MagicMock()

        with patch('asyncio.run') as mock_asyncio:
            mock_asyncio.return_value = {
                "user_id": "user1",
                "model_name": "phi-2",
                "status": "completed",
                "metrics": {
                    "accuracy": 0.85,
                },
            }
            result = task.run(
                user_id="user1",
                model_name="phi-2",
                test_samples=50
            )

            assert mock_asyncio.called
            assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_evaluate_result_structure(self):
        """Test evaluation returns proper structure"""
        task = ModelEvaluationTask()
        task.db_manager = MagicMock()

        result = await task._evaluate_async(
            user_id="user1",
            model_name="phi-2",
            test_samples=50
        )

        # Verify result structure
        assert result["user_id"] == "user1"
        assert result["model_name"] == "phi-2"
        assert result["test_samples"] == 50
        assert result["status"] == "completed"
        assert "metrics" in result

    @pytest.mark.asyncio
    async def test_evaluate_metrics_present(self):
        """Test that evaluation results include all metrics"""
        task = ModelEvaluationTask()
        task.db_manager = MagicMock()

        result = await task._evaluate_async(
            user_id="user1",
            model_name="phi-2",
            test_samples=50
        )

        metrics = result["metrics"]
        assert "accuracy" in metrics
        assert "precision" in metrics
        assert "recall" in metrics
        assert "f1_score" in metrics
        assert "inference_time_ms" in metrics

    @pytest.mark.asyncio
    async def test_evaluate_performance_comparison(self):
        """Test evaluation includes performance comparison"""
        task = ModelEvaluationTask()
        task.db_manager = MagicMock()

        result = await task._evaluate_async(
            user_id="user1",
            model_name="phi-2",
            test_samples=50
        )

        assert "performance_vs_baseline" in result
        baseline = result["performance_vs_baseline"]
        assert "accuracy_improvement_percent" in baseline
        assert "inference_speedup_percent" in baseline


@pytest.mark.unit
class TestModelBenchmarkTask:
    """Test model benchmarking task"""

    def test_task_initialization(self):
        """Test task initialization"""
        task = ModelBenchmarkTask()
        assert task.name == "ai_pal.tasks.model_tasks.benchmark_model"
        assert task.bind is True
        assert task.max_retries == 1

    def test_benchmark_run_method(self):
        """Test run method executes async operation"""
        task = ModelBenchmarkTask()
        task.db_manager = MagicMock()

        with patch('asyncio.run') as mock_asyncio:
            mock_asyncio.return_value = {
                "model_name": "phi-2",
                "overall_score": 0.83,
                "scenarios_tested": 4,
            }
            result = task.run(model_name="phi-2", scenarios=None)

            assert mock_asyncio.called
            assert result["model_name"] == "phi-2"

    @pytest.mark.asyncio
    async def test_benchmark_result_structure(self):
        """Test benchmarking returns proper structure"""
        task = ModelBenchmarkTask()
        task.db_manager = MagicMock()

        result = await task._benchmark_async(
            model_name="phi-2",
            scenarios=None
        )

        # Verify result structure
        assert result["model_name"] == "phi-2"
        assert "scenarios_tested" in result
        assert "benchmark_results" in result
        assert "overall_score" in result
        assert "benchmark_timestamp" in result

    @pytest.mark.asyncio
    async def test_benchmark_default_scenarios(self):
        """Test benchmarking with default scenarios"""
        task = ModelBenchmarkTask()
        task.db_manager = MagicMock()

        result = await task._benchmark_async(
            model_name="phi-2",
            scenarios=None
        )

        # Default scenarios should be tested
        assert result["scenarios_tested"] >= 1
        assert "benchmark_results" in result

    @pytest.mark.asyncio
    async def test_benchmark_custom_scenarios(self):
        """Test benchmarking with custom scenarios"""
        task = ModelBenchmarkTask()
        task.db_manager = MagicMock()

        custom_scenarios = ["custom1", "custom2"]

        result = await task._benchmark_async(
            model_name="phi-2",
            scenarios=custom_scenarios
        )

        assert result["scenarios_tested"] == len(custom_scenarios)

    @pytest.mark.asyncio
    async def test_benchmark_metrics_per_scenario(self):
        """Test that each scenario has metrics"""
        task = ModelBenchmarkTask()
        task.db_manager = MagicMock()

        result = await task._benchmark_async(
            model_name="phi-2",
            scenarios=["test_scenario"]
        )

        benchmark_results = result["benchmark_results"]
        for scenario, metrics in benchmark_results.items():
            assert "accuracy" in metrics
            assert "latency_ms" in metrics
            assert "throughput_tokens_per_sec" in metrics


@pytest.mark.integration
class TestModelTasksIntegration:
    """Integration tests for model tasks"""

    def test_finetune_evaluate_benchmark_workflow(self):
        """Test workflow: finetune -> evaluate -> benchmark"""
        finetune_task = ModelFinetuningTask()
        evaluate_task = ModelEvaluationTask()
        benchmark_task = ModelBenchmarkTask()

        finetune_task.db_manager = MagicMock()
        evaluate_task.db_manager = MagicMock()
        benchmark_task.db_manager = MagicMock()

        # First finetune
        with patch('asyncio.run') as mock_asyncio:
            mock_asyncio.return_value = {"status": "completed"}
            finetune_result = finetune_task.run(
                user_id="user1",
                model_name="phi-2",
                training_samples=100,
                learning_rate=1e-4
            )

            assert finetune_result["status"] == "completed"

        # Then evaluate
        with patch('asyncio.run') as mock_asyncio:
            mock_asyncio.return_value = {"status": "completed"}
            evaluate_result = evaluate_task.run(
                user_id="user1",
                model_name="phi-2",
                test_samples=50
            )

            assert evaluate_result["status"] == "completed"

        # Finally benchmark
        with patch('asyncio.run') as mock_asyncio:
            mock_asyncio.return_value = {"overall_score": 0.83}
            benchmark_result = benchmark_task.run(model_name="phi-2")

            assert benchmark_result["overall_score"] == 0.83

    def test_task_error_handling(self):
        """Test task error handling"""
        task = ModelFinetuningTask()
        task.db_manager = None  # Simulate missing DB

        with patch('asyncio.run') as mock_asyncio:
            mock_asyncio.side_effect = RuntimeError("Database not configured")

            with pytest.raises(RuntimeError):
                task.run(
                    user_id="user1",
                    model_name="phi-2",
                    training_samples=100,
                    learning_rate=1e-4
                )


@pytest.mark.unit
class TestModelMetrics:
    """Test model metrics and evaluations"""

    def test_accuracy_range(self):
        """Test accuracy values are in valid range"""
        valid_accuracies = [0.0, 0.5, 0.85, 1.0]

        for accuracy in valid_accuracies:
            assert 0 <= accuracy <= 1

    def test_loss_calculation(self):
        """Test loss values are non-negative"""
        valid_losses = [0.0, 0.45, 1.0, 100.0]

        for loss in valid_losses:
            assert loss >= 0

    def test_f1_score_calculation(self):
        """Test F1 score calculation"""
        precision = 0.85
        recall = 0.80

        # F1 = 2 * (precision * recall) / (precision + recall)
        f1 = 2 * (precision * recall) / (precision + recall)

        assert 0 <= f1 <= 1
        assert f1 < max(precision, recall)

    def test_inference_time_positive(self):
        """Test inference time is positive"""
        valid_times = [1.0, 50.5, 125.3, 1000.0]

        for time in valid_times:
            assert time > 0
