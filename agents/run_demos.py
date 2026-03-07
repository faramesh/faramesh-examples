#!/usr/bin/env python3
"""
Master Demo Runner - Run All Faramesh Demos

This script provides an interactive menu to run all Faramesh security demos.
Each demo showcases a specific security capability across different agent frameworks.
"""

import os
import sys
import subprocess


DEMOS = [
    {
        "id": 1,
        "name": "Float Canonicalization",
        "script": "05_float_canonicalization.py",
        "description": "Show how 1.0, 1.00, and 1 produce identical hashes",
        "time": "3 min",
        "framework": "Core",
    },
    {
        "id": 2,
        "name": "LangChain Delete-All Prevention",
        "script": "01_langchain_delete_all.py",
        "description": "Stop dangerous 'rm -rf /' hallucinations",
        "time": "5 min",
        "framework": "LangChain",
    },
    {
        "id": 3,
        "name": "Customer Service Discount Control",
        "script": "08_customer_service_discount.py",
        "description": "Prevent 100% discounts (eBay/Artium case)",
        "time": "5 min",
        "framework": "Business",
    },
    {
        "id": 4,
        "name": "AutoGen High-Value Approval",
        "script": "03_autogen_high_value_approval.py",
        "description": "Human-in-the-loop for $1,000+ transactions",
        "time": "5 min",
        "framework": "AutoGen",
    },
    {
        "id": 5,
        "name": "MCP Filesystem Security",
        "script": "04_mcp_filesystem_security.py",
        "description": "Secure Model Context Protocol filesystem server",
        "time": "5 min",
        "framework": "MCP",
    },
    {
        "id": 6,
        "name": "CrewAI Infinite Loop Prevention",
        "script": "02_crewai_infinite_loop.py",
        "description": "Stop multi-agent infinite delegation loops",
        "time": "4 min",
        "framework": "CrewAI",
    },
    {
        "id": 7,
        "name": "Zero-Trust Cryptographic Audit",
        "script": "06_zero_trust_crypto.py",
        "description": "Show SHA-256 hashing and provenance IDs",
        "time": "4 min",
        "framework": "Core",
    },
    {
        "id": 8,
        "name": "Latency Benchmark",
        "script": "07_latency_benchmark.py",
        "description": "Measure <2ms overhead for local deployment",
        "time": "3 min",
        "framework": "Performance",
    },
    {
        "id": 9,
        "name": "Healthcare PII Redaction",
        "script": "09_healthcare_pii_redaction.py",
        "description": "Detect and redact SSN/PII from tool calls",
        "time": "4 min",
        "framework": "Healthcare",
    },
    {
        "id": 10,
        "name": "DevOps Security (ls vs rm -rf)",
        "script": "10_devops_security.py",
        "description": "Surgical command filtering for DevOps",
        "time": "5 min",
        "framework": "DevOps",
    },
]


def print_header():
    """Print fancy header."""
    print("\n" + "=" * 80)
    print("🚀 Faramesh Security Demo Suite")
    print("=" * 80)
    print()
    print(
        "Complete demonstration of Faramesh's agent security and governance capabilities"
    )
    print("across multiple frameworks: LangChain, AutoGen, CrewAI, MCP, and more.")
    print()


def print_menu():
    """Print demo menu."""
    print("-" * 80)
    print("Available Demos:")
    print("-" * 80)
    print()

    for demo in DEMOS:
        print(f"{demo['id']:2}. [{demo['framework']:12}] {demo['name']}")
        print(f"    {demo['description']}")
        print(f"    Time: {demo['time']}")
        print()

    print("-" * 80)
    print("Options:")
    print("  - Enter demo number (1-10) to run single demo")
    print("  - Enter 'all' to run all demos sequentially")
    print("  - Enter 'quick' for 5-minute quick demo (1, 2, 3)")
    print("  - Enter 'full' for 40-minute full showcase (all demos)")
    print("  - Enter 'q' to quit")
    print("-" * 80)


def run_demo(demo):
    """Run a single demo."""
    demo_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(demo_dir, demo["script"])

    if not os.path.exists(script_path):
        print(f"\n❌ Error: Demo script not found: {script_path}")
        return False

    print(f"\n{'=' * 80}")
    print(f"🎬 Running Demo {demo['id']}: {demo['name']}")
    print(f"{'=' * 80}\n")

    try:
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=demo_dir,
            check=False,
        )

        if result.returncode == 0:
            print(f"\n✅ Demo {demo['id']} completed successfully")
            return True
        else:
            print(f"\n⚠️  Demo {demo['id']} exited with code {result.returncode}")
            return False

    except KeyboardInterrupt:
        print(f"\n\n⚠️  Demo {demo['id']} interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Error running demo {demo['id']}: {e}")
        return False


def run_quick_demo():
    """Run 5-minute quick demo."""
    print("\n🏃 Running Quick Demo (5 minutes)")
    print("Demos: Float Canonicalization, LangChain, Customer Service")
    print()

    quick_demos = [d for d in DEMOS if d["id"] in [1, 2, 3]]

    for demo in quick_demos:
        run_demo(demo)
        input("\n➡️  Press Enter to continue to next demo...")


def run_full_showcase():
    """Run full 40-minute showcase."""
    print("\n🎭 Running Full Showcase (40 minutes)")
    print("All 10 demos will run sequentially")
    print()

    results = []

    for demo in DEMOS:
        success = run_demo(demo)
        results.append({"demo": demo["name"], "success": success})

        if demo["id"] < len(DEMOS):
            input("\n➡️  Press Enter to continue to next demo...")

    # Summary
    print("\n" + "=" * 80)
    print("📊 Full Showcase Summary")
    print("=" * 80)
    print()

    successful = sum(1 for r in results if r["success"])
    total = len(results)

    print(f"Completed: {successful}/{total} demos")
    print()

    if successful == total:
        print("✅ All demos completed successfully!")
    else:
        print("⚠️  Some demos had issues:")
        for r in results:
            if not r["success"]:
                print(f"   - {r['demo']}")


def run_all_demos():
    """Run all demos without pauses."""
    print("\n🏁 Running All Demos")
    print()

    for demo in DEMOS:
        run_demo(demo)
        print()


def check_prerequisites():
    """Check if Faramesh server is running."""
    import urllib.request
    import urllib.error

    try:
        url = os.getenv("FARAMESH_URL", "http://localhost:8000") + "/health"
        urllib.request.urlopen(url, timeout=2)
        print("✅ Faramesh server is running")
        return True
    except (urllib.error.URLError, Exception):
        print("⚠️  Warning: Faramesh server may not be running")
        print(
            "   Start server: cd faramesh-horizon-code && python -m faramesh.server.main"
        )
        print()
        response = input("Continue anyway? (y/n): ").strip().lower()
        return response == "y"


def main():
    """Main interactive loop."""
    print_header()

    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Exiting...")
        sys.exit(1)

    while True:
        print_menu()

        choice = input("\nEnter your choice: ").strip().lower()

        if choice == "q":
            print("\n👋 Goodbye!")
            break

        elif choice == "all":
            run_all_demos()
            input("\n➡️  Press Enter to return to menu...")

        elif choice == "quick":
            run_quick_demo()
            input("\n➡️  Press Enter to return to menu...")

        elif choice == "full":
            run_full_showcase()
            input("\n➡️  Press Enter to return to menu...")

        elif choice.isdigit():
            demo_id = int(choice)
            demo = next((d for d in DEMOS if d["id"] == demo_id), None)

            if demo:
                run_demo(demo)
                input("\n➡️  Press Enter to return to menu...")
            else:
                print(f"\n❌ Invalid demo number: {demo_id}")
                input("\nPress Enter to continue...")

        else:
            print(f"\n❌ Invalid choice: {choice}")
            input("\nPress Enter to continue...")

        # Clear screen (optional)
        # os.system('clear' if os.name == 'posix' else 'cls')


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user. Goodbye!")
        sys.exit(0)
