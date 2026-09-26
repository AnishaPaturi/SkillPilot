"""Tests for Phase 10 Evaluation Benchmark Suite."""
import pytest
from app.evaluation.dataset import get_benchmark_dataset
from app.evaluation.benchmark import EvaluationBenchmark
from app.skills.registry import SkillRegistry


@pytest.fixture
def benchmark():
    return EvaluationBenchmark()


def test_benchmark_dataset_integrity():
    """Verify benchmark dataset adheres to the Phase 10 specifications."""
    dataset = get_benchmark_dataset()

    # 1. Total query count must be exactly 20
    assert len(dataset) == 20

    # 2. Check unique IDs from 1 to 20
    ids = [item.id for item in dataset]
    assert sorted(ids) == list(range(1, 21))

    # 3. Check category breakdown
    negatives = [item for item in dataset if item.is_negative]
    assert len(negatives) == 3

    multi_skills = [item for item in dataset if item.category == "multi_skill_chaining"]
    assert len(multi_skills) == 2

    # Verify each of the 5 skills has single-skill queries
    single_categories = {item.category for item in dataset if not item.is_negative and item.category != "multi_skill_chaining"}
    assert single_categories == {
        "code_analysis",
        "security_analysis",
        "documentation",
        "code_explanation",
        "task_planning",
    }


def test_benchmark_skill_selection_accuracy(benchmark):
    """Verify skill selection accuracy meets the high standard (>= 95%)."""
    summary = benchmark.evaluate_router_only()
    assert summary.skill_selection_accuracy >= 95.0, (
        f"Skill Selection Accuracy {summary.skill_selection_accuracy}% was below 95% threshold"
    )


def test_benchmark_invalid_request_handling(benchmark):
    """Verify that off-domain/unsupported requests are strictly rejected (100% rejection rate)."""
    summary = benchmark.evaluate_router_only()
    assert summary.invalid_request_handling == 100.0, (
        f"Invalid Request Handling {summary.invalid_request_handling}% was below 100%"
    )


def test_benchmark_multi_skill_accuracy(benchmark):
    """Verify multi-skill workflow chains are sequenced correctly (100% chaining fidelity)."""
    summary = benchmark.evaluate_router_only()
    assert summary.multi_skill_accuracy == 100.0, (
        f"Multi-Skill Accuracy {summary.multi_skill_accuracy}% was below 100%"
    )


def test_benchmark_latency_metrics(benchmark):
    """Verify latency metrics are properly computed and reasonable."""
    summary = benchmark.evaluate_router_only()
    assert summary.avg_latency_ms > 0
    assert summary.min_latency_ms > 0
    assert summary.max_latency_ms >= summary.min_latency_ms
    assert summary.p95_latency_ms >= summary.min_latency_ms
    assert summary.total_time_seconds > 0


def test_benchmark_json_export(benchmark, tmp_path):
    """Verify benchmark results can be exported to JSON telemetry."""
    summary = benchmark.evaluate_router_only()
    export_file = tmp_path / "evaluation_telemetry.json"
    benchmark.export_json(summary, str(export_file))

    assert export_file.exists()
    import json
    with open(export_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["total_queries"] == 20
    assert "skill_selection_accuracy" in data
    assert len(data["results"]) == 20
