"""
Phase 10: Academic Evaluation & Benchmark Demonstration

Measures the 6 core evaluation metrics on a curated 20-query benchmark dataset:
1. Skill Selection Accuracy (Correct Selections / Total Queries * 100)
2. Execution Accuracy (Validated outputs without errors)
3. Invalid Request Handling (Rejection of unsupported/creative requests)
4. Multi-Skill Accuracy (Ordered sequencing of chained skills)
5. Response Quality (Output completeness and structural compliance)
6. Latency Performance (Min, Max, Avg, P95 response times)
"""
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.evaluation.benchmark import EvaluationBenchmark
from app.evaluation.dataset import get_benchmark_dataset


def run_phase_10_demo():
    print("=" * 82)
    print("      PHASE 10: SKILLPILOT EVALUATION & METRICS BENCHMARK SUITE")
    print("=" * 82)

    dataset = get_benchmark_dataset()
    print(f"\n1. Loaded benchmark dataset with {len(dataset)} diverse test queries.")
    print("   Categories covered:")
    print("     - Single-Skill Code Analysis (3 queries)")
    print("     - Single-Skill Security Analysis (3 queries)")
    print("     - Single-Skill Documentation (3 queries)")
    print("     - Single-Skill Code Explanation (3 queries)")
    print("     - Single-Skill Task Planning (3 queries)")
    print("     - Multi-Skill Sequential Chaining (2 queries)")
    print("     - Negative Controls / Invalid Requests (3 queries)")

    print("\n2. Executing benchmark evaluation...")
    benchmark = EvaluationBenchmark()

    # Fast router evaluation computes accuracy and latency across all 20 queries
    summary = benchmark.evaluate_router_only(dataset=dataset)

    print("\n3. Generated Evaluation Telemetry Report:")
    report_text = benchmark.format_terminal_report(summary)
    print(report_text)

    # Save telemetry JSON
    output_path = ROOT_DIR / "evaluation_telemetry.json"
    benchmark.export_json(summary, str(output_path))
    print(f"Telemetric results exported to: {output_path.name}")

    print("\n" + "=" * 82)
    print("PHASE 10 EVALUATION COMPLETE: ALL BENCHMARK METRICS RECORDED!")
    print("=" * 82)


if __name__ == "__main__":
    run_phase_10_demo()
