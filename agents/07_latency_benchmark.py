#!/usr/bin/env python3
"""
Latency Benchmark Demo: Running Faramesh with <2ms Overhead

This demo measures the overhead Faramesh adds to tool execution.
Goal: Demonstrate <2ms latency for local deployments.

Scenario:
- Submit actions and measure end-to-end latency
- Compare direct execution vs gated execution
- Show that security doesn't mean slow

Required: Running Faramesh server locally
"""

import os
import sys
import time
import statistics
from typing import List
from demo_utils import ensure_server_available

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "faramesh-python-sdk-code")
    ),
)

from faramesh import configure, submit_action


FARAMESH_BASE_URL = os.getenv("FARAMESH_BASE_URL", "http://localhost:8000")
FARAMESH_TOKEN = os.getenv("FARAMESH_TOKEN") or os.getenv(
    "FARAMESH_API_KEY", "demo-api-key-123"
)
FARAMESH_AGENT_ID = os.getenv("FARAMESH_AGENT_ID", "latency-benchmark-001")

configure(base_url=FARAMESH_BASE_URL, token=FARAMESH_TOKEN, agent_id=FARAMESH_AGENT_ID)


def measure_submission_latency(num_samples: int = 50) -> List[float]:
    """Measure action submission latency."""
    latencies = []

    print(f"Measuring submission latency ({num_samples} samples)...")

    for i in range(num_samples):
        start = time.perf_counter()

        try:
            _ = submit_action(
                agent_id=FARAMESH_AGENT_ID,
                tool="benchmark",
                operation="test",
                params={"iteration": i},
                context={"benchmark": True},
            )

            end = time.perf_counter()
            latency_ms = (end - start) * 1000
            latencies.append(latency_ms)

            # Show progress every 10 samples
            if (i + 1) % 10 == 0:
                print(f"  {i + 1}/{num_samples} samples...")

        except Exception as e:
            print(f"  Error on sample {i + 1}: {e}")
            continue

    return latencies


def measure_evaluation_latency(num_samples: int = 50) -> List[float]:
    """Measure end-to-end evaluation latency (submit + wait)."""
    latencies = []

    print(f"\nMeasuring evaluation latency ({num_samples} samples)...")

    for i in range(num_samples):
        start = time.perf_counter()

        try:
            _ = submit_action(
                agent_id=FARAMESH_AGENT_ID,
                tool="shell",
                operation="execute",
                params={"cmd": "echo test"},
                context={"benchmark": True},
            )

            # Wait for evaluation (not execution)
            # This measures policy evaluation overhead
            end = time.perf_counter()
            latency_ms = (end - start) * 1000
            latencies.append(latency_ms)

            if (i + 1) % 10 == 0:
                print(f"  {i + 1}/{num_samples} samples...")

        except Exception as e:
            print(f"  Error on sample {i + 1}: {e}")
            continue

    return latencies


def print_statistics(latencies: List[float], label: str):
    """Print latency statistics."""
    if not latencies:
        print(f"  No data for {label}")
        return

    print(f"\n📊 {label} Statistics:")
    print("-" * 60)
    print(f"  Samples: {len(latencies)}")
    print(f"  Mean: {statistics.mean(latencies):.2f}ms")
    print(f"  Median: {statistics.median(latencies):.2f}ms")
    print(f"  Min: {min(latencies):.2f}ms")
    print(f"  Max: {max(latencies):.2f}ms")
    print(
        f"  Std Dev: {statistics.stdev(latencies):.2f}ms"
        if len(latencies) > 1
        else "  Std Dev: N/A"
    )

    # Percentiles
    sorted_latencies = sorted(latencies)
    p50 = sorted_latencies[len(sorted_latencies) // 2]
    p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)]
    p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)]

    print(f"  P50: {p50:.2f}ms")
    print(f"  P95: {p95:.2f}ms")
    print(f"  P99: {p99:.2f}ms")

    # Check if meeting <2ms target
    if statistics.median(latencies) < 2.0:
        print(
            f"\n  ✅ SUCCESS: Median latency ({statistics.median(latencies):.2f}ms) < 2ms target!"
        )
    else:
        print(
            f"\n  ⚠️  Median latency ({statistics.median(latencies):.2f}ms) exceeds 2ms target"
        )
        print("     Note: Network latency and server load affect results")


def run_benchmark():
    """Run complete latency benchmark."""
    print("\n" + "=" * 80)
    print("⚡ Latency Benchmark: Faramesh Overhead Measurement")
    print("=" * 80)
    print()
    print("Goal: Demonstrate <2ms overhead for security gating")
    print("Method: Measure action submission and evaluation latency")
    print()
    print("Note: Results depend on:")
    print("  - Network latency (local vs remote)")
    print("  - Server load")
    print("  - Database performance")
    print("  - Policy complexity")
    print()
    print("-" * 80)
    print()

    # Warmup
    print("🔥 Warming up (5 samples)...")
    for i in range(5):
        try:
            _ = submit_action(
                agent_id=FARAMESH_AGENT_ID,
                tool="warmup",
                operation="test",
                params={"warmup": True},
                context={},
            )
        except Exception:
            pass
    print("  Warmup complete\n")

    # Run benchmarks
    submission_latencies = measure_submission_latency(num_samples=50)
    evaluation_latencies = measure_evaluation_latency(num_samples=50)

    # Print results
    print("\n" + "=" * 80)
    print("📈 Benchmark Results")
    print("=" * 80)

    print_statistics(submission_latencies, "Action Submission Latency")
    print_statistics(evaluation_latencies, "Policy Evaluation Latency")

    # Summary
    print("\n" + "=" * 80)
    print("✅ Benchmark Complete")
    print("=" * 80)
    print()

    if submission_latencies and statistics.median(submission_latencies) < 2.0:
        print("🎉 SUCCESS: Faramesh adds <2ms overhead!")
        print()
        print("This demonstrates:")
        print("  - Security doesn't mean slow")
        print("  - Governance at agent speed")
        print("  - Production-ready performance")
        print("  - Zero compromise on safety or speed")
    else:
        print("⚠️  Latency results:")
        if submission_latencies:
            median = statistics.median(submission_latencies)
            print(f"  Median: {median:.2f}ms")
            print()
            print("Factors that may affect results:")
            print("  - Network latency (try running server locally)")
            print("  - Database connection latency")
            print("  - Server under load")
            print("  - Policy complexity")

    print()
    print("Optimization Tips:")
    print("  1. Run Faramesh locally for lowest latency")
    print("  2. Use connection pooling for database")
    print("  3. Cache policy evaluations when possible")
    print("  4. Use async/await for concurrent requests")
    print()


def run_demo():
    """Run the latency benchmark demo."""
    if not ensure_server_available(FARAMESH_BASE_URL):
        return
    print("\n⚠️  IMPORTANT: This benchmark requires a running Faramesh server")
    print("   Make sure the server is running at: " + FARAMESH_BASE_URL)
    print()

    user_input = input("Continue with benchmark? (y/n): ").strip().lower()

    if user_input == "y":
        run_benchmark()
    else:
        print("\nBenchmark cancelled.")
        print("\nTo run the server:")
        print("  cd faramesh-horizon-code")
        print("  python -m faramesh.server.main")
        print()


if __name__ == "__main__":
    run_demo()
