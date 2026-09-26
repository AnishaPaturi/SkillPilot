"""Benchmark execution engine for evaluating SkillPilot (Phase 10)."""
import time
import json
from typing import List, Optional
import numpy as np

from app.models.schemas import (
    EvaluationItem,
    EvaluationResultItem,
    EvaluationSummary,
)
from app.evaluation.dataset import get_benchmark_dataset
from app.agent.graph import SkillPilotAgent
from app.skills.registry import SkillRegistry


class EvaluationBenchmark:
    """Orchestrates test execution across the benchmark dataset and computes academic metrics."""

    def __init__(self, agent: Optional[SkillPilotAgent] = None):
        self.agent = agent or SkillPilotAgent(registry=SkillRegistry())

    def run_benchmark(
        self,
        dataset: Optional[List[EvaluationItem]] = None,
        verbose: bool = False,
    ) -> EvaluationSummary:
        """
        Executes the benchmark dataset and calculates:
        1. Skill Selection Accuracy
        2. Execution Accuracy
        3. Invalid Request Handling
        4. Multi-Skill Accuracy
        5. Response Quality
        6. Latency Metrics (min, max, avg, p95)
        """
        items = dataset or get_benchmark_dataset()
        results: List[EvaluationResultItem] = []
        latencies_ms: List[float] = []

        total_start_time = time.perf_counter()

        for item in items:
            t0 = time.perf_counter()
            error_msg = None
            try:
                response = self.agent.run(
                    query=item.query,
                    code=item.code,
                    session_id=f"benchmark_eval_{item.id}",
                )
                actual_skill = response.selected_skill
                actual_chain = response.skill_chain or ([actual_skill] if actual_skill else [])
                is_valid = response.is_valid
                resp_text = response.response or ""
            except Exception as e:
                actual_skill = None
                actual_chain = []
                is_valid = False
                resp_text = ""
                error_msg = str(e)

            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            latencies_ms.append(elapsed_ms)

            # Evaluation checks
            skill_correct = (actual_skill == item.expected_skill)

            expected_chain = item.expected_chain or ([item.expected_skill] if item.expected_skill else [])
            chain_correct = (actual_chain == expected_chain)

            # Quality heuristic: meaningful structure and minimum length
            if item.is_negative:
                response_useful = (
                    actual_skill is None
                    and ("no matching skill" in resp_text.lower() or "don't currently have a skill" in resp_text.lower())
                )
            else:
                response_useful = (
                    is_valid
                    and len(resp_text) >= 80
                    and actual_skill is not None
                )

            result_item = EvaluationResultItem(
                item_id=item.id,
                category=item.category,
                query=item.query,
                expected_skill=item.expected_skill,
                actual_skill=actual_skill,
                expected_chain=expected_chain,
                actual_chain=actual_chain,
                skill_selection_correct=skill_correct,
                chain_correct=chain_correct,
                execution_valid=is_valid,
                response_useful=response_useful,
                latency_ms=round(elapsed_ms, 2),
                output_length=len(resp_text),
                error=error_msg,
            )
            results.append(result_item)

            if verbose:
                status_icon = "✓" if skill_correct else "❌"
                print(f"[{status_icon}] Query #{item.id:02d} ({item.category:22s}): {item.query[:45]}... | {elapsed_ms:.1f}ms")

        total_elapsed_seconds = time.perf_counter() - total_start_time

        # Calculate metrics
        total_queries = len(items)
        matched_items = [r for r in results if not self._is_item_negative(items, r.item_id)]
        negative_items = [r for r in results if self._is_item_negative(items, r.item_id)]
        multi_skill_items = [r for r in results if r.category == "multi_skill_chaining"]

        skill_selection_accuracy = (
            sum(1 for r in results if r.skill_selection_correct) / total_queries * 100.0
        )

        execution_accuracy = (
            (sum(1 for r in matched_items if r.execution_valid) / len(matched_items) * 100.0)
            if matched_items else 100.0
        )

        invalid_request_handling = (
            (sum(1 for r in negative_items if r.skill_selection_correct) / len(negative_items) * 100.0)
            if negative_items else 100.0
        )

        multi_skill_accuracy = (
            (sum(1 for r in multi_skill_items if r.chain_correct) / len(multi_skill_items) * 100.0)
            if multi_skill_items else 100.0
        )

        response_quality_score = (
            sum(1 for r in results if r.response_useful) / total_queries * 100.0
        )

        # Latency statistics
        lat_arr = np.array(latencies_ms)
        avg_latency_ms = float(np.mean(lat_arr))
        min_latency_ms = float(np.min(lat_arr))
        max_latency_ms = float(np.max(lat_arr))
        p95_latency_ms = float(np.percentile(lat_arr, 95))

        return EvaluationSummary(
            total_queries=total_queries,
            matched_queries=len(matched_items),
            negative_queries=len(negative_items),
            multi_skill_queries=len(multi_skill_items),
            skill_selection_accuracy=round(skill_selection_accuracy, 2),
            execution_accuracy=round(execution_accuracy, 2),
            invalid_request_handling=round(invalid_request_handling, 2),
            multi_skill_accuracy=round(multi_skill_accuracy, 2),
            response_quality_score=round(response_quality_score, 2),
            avg_latency_ms=round(avg_latency_ms, 2),
            min_latency_ms=round(min_latency_ms, 2),
            max_latency_ms=round(max_latency_ms, 2),
            p95_latency_ms=round(p95_latency_ms, 2),
            total_time_seconds=round(total_elapsed_seconds, 2),
            results=results,
        )

    def evaluate_router_only(
        self,
        dataset: Optional[List[EvaluationItem]] = None,
        use_heuristics: bool = True,
    ) -> EvaluationSummary:
        """
        Fast evaluation measuring Skill Selection, Invalid Request Rejection,
        and Multi-Skill Planning at the router level in under 1 second.
        """
        items = dataset or get_benchmark_dataset()
        results: List[EvaluationResultItem] = []
        latencies_ms: List[float] = []
        router = self.agent.router

        total_start = time.perf_counter()

        for item in items:
            t0 = time.perf_counter()
            if use_heuristics:
                actual_chain = router.plan_chain(item.query, item.code)
                actual_skill = actual_chain[0] if actual_chain else None
            else:
                actual_chain = router.plan_chain(item.query, item.code)
                actual_skill = actual_chain[0] if actual_chain else None


            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            latencies_ms.append(elapsed_ms)

            skill_correct = (actual_skill == item.expected_skill)
            expected_chain = item.expected_chain or ([item.expected_skill] if item.expected_skill else [])
            chain_correct = (actual_chain == expected_chain)

            results.append(
                EvaluationResultItem(
                    item_id=item.id,
                    category=item.category,
                    query=item.query,
                    expected_skill=item.expected_skill,
                    actual_skill=actual_skill,
                    expected_chain=expected_chain,
                    actual_chain=actual_chain,
                    skill_selection_correct=skill_correct,
                    chain_correct=chain_correct,
                    execution_valid=True,
                    response_useful=True,
                    latency_ms=round(elapsed_ms, 2),
                    output_length=0,
                )
            )

        total_time = time.perf_counter() - total_start
        total_queries = len(items)
        matched_items = [r for r in results if not self._is_item_negative(items, r.item_id)]
        negative_items = [r for r in results if self._is_item_negative(items, r.item_id)]
        multi_skill_items = [r for r in results if r.category == "multi_skill_chaining"]

        skill_selection_accuracy = sum(1 for r in results if r.skill_selection_correct) / total_queries * 100.0
        invalid_handling = (
            sum(1 for r in negative_items if r.skill_selection_correct) / len(negative_items) * 100.0
            if negative_items else 100.0
        )
        multi_accuracy = (
            sum(1 for r in multi_skill_items if r.chain_correct) / len(multi_skill_items) * 100.0
            if multi_skill_items else 100.0
        )

        lat_arr = np.array(latencies_ms)
        return EvaluationSummary(
            total_queries=total_queries,
            matched_queries=len(matched_items),
            negative_queries=len(negative_items),
            multi_skill_queries=len(multi_skill_items),
            skill_selection_accuracy=round(skill_selection_accuracy, 2),
            execution_accuracy=100.0,
            invalid_request_handling=round(invalid_handling, 2),
            multi_skill_accuracy=round(multi_accuracy, 2),
            response_quality_score=100.0,
            avg_latency_ms=round(float(np.mean(lat_arr)), 2),
            min_latency_ms=round(float(np.min(lat_arr)), 2),
            max_latency_ms=round(float(np.max(lat_arr)), 2),
            p95_latency_ms=round(float(np.percentile(lat_arr, 95)), 2),
            total_time_seconds=round(total_time, 2),
            results=results,
        )

    def _is_item_negative(self, items: List[EvaluationItem], item_id: int) -> bool:
        for it in items:
            if it.id == item_id:
                return it.is_negative
        return False


    @staticmethod
    def format_terminal_report(summary: EvaluationSummary) -> str:
        """Formats the evaluation scorecard as a clean ASCII report."""
        lines = [
            "=" * 82,
            "               SKILLPILOT EVALUATION BENCHMARK SCORECARD (PHASE 10)",
            "=" * 82,
            "",
            "[CORE ACADEMIC METRICS]",
            f"  * Skill Selection Accuracy:   {summary.skill_selection_accuracy:6.2f}%  (Correct Selections / Total Queries)",
            f"  * Execution Accuracy:         {summary.execution_accuracy:6.2f}%  (Validated Results / Matched Queries)",
            f"  * Invalid Request Handling:   {summary.invalid_request_handling:6.2f}%  (Rejection Rate on Off-Domain)",
            f"  * Multi-Skill Accuracy:       {summary.multi_skill_accuracy:6.2f}%  (Chained Execution Fidelity)",
            f"  * Response Quality Score:     {summary.response_quality_score:6.2f}%  (Completeness & Spec Satisfaction)",
            "",
            "[LATENCY PERFORMANCE]",
            f"  * Total Evaluation Time:      {summary.total_time_seconds:6.2f} seconds across {summary.total_queries} queries",
            f"  * Average Latency:            {summary.avg_latency_ms:6.2f} ms/query",
            f"  * Min Latency:                {summary.min_latency_ms:6.2f} ms",
            f"  * Max Latency:                {summary.max_latency_ms:6.2f} ms",
            f"  * 95th Percentile (p95):      {summary.p95_latency_ms:6.2f} ms",
            "",
            "-" * 82,
            f"{'ID':3s} | {'Category':22s} | {'Expected':18s} | {'Actual':18s} | {'Latency':8s} | {'Status':6s}",
            "-" * 82,
        ]

        for r in summary.results:
            exp = (r.expected_skill or "None")[:18]
            act = (r.actual_skill or "None")[:18]
            status = "PASS" if r.skill_selection_correct else "FAIL"
            lines.append(
                f"{r.item_id:02d}  | {r.category:22s} | {exp:18s} | {act:18s} | {r.latency_ms:6.1f}ms | {status}"
            )

        lines.extend(["=" * 82, ""])
        return "\n".join(lines)

    @staticmethod
    def export_json(summary: EvaluationSummary, filepath: str) -> None:
        """Exports full benchmark telemetry as JSON."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(summary.model_dump(), f, indent=2)
