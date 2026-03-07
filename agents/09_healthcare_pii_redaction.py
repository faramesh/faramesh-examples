#!/usr/bin/env python3
"""
Healthcare PII Redaction Demo: Redacting Social Security Numbers

This demo shows how Faramesh can detect and redact PII (Personally
Identifiable Information) from tool calls before they're logged or executed.

Scenario:
- Healthcare AI agent processes patient data
- Agent accidentally includes SSN in API call
- Faramesh detects SSN pattern and redacts it
- Audit trail shows redacted version, original never stored

Required Policy: healthcare_pii_policy.yaml
"""

import os
import sys
import re
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
FARAMESH_AGENT_ID = os.getenv("FARAMESH_AGENT_ID", "healthcare-agent-001")

configure(base_url=FARAMESH_BASE_URL, token=FARAMESH_TOKEN, agent_id=FARAMESH_AGENT_ID)


# PII Detection Patterns
SSN_PATTERN = r"\b\d{3}-\d{2}-\d{4}\b"
CREDIT_CARD_PATTERN = r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"
PHONE_PATTERN = r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"


def detect_pii(text: str) -> dict:
    """Detect PII in text."""
    findings = {}

    if re.search(SSN_PATTERN, text):
        findings["ssn"] = re.findall(SSN_PATTERN, text)

    if re.search(CREDIT_CARD_PATTERN, text):
        findings["credit_card"] = re.findall(CREDIT_CARD_PATTERN, text)

    if re.search(PHONE_PATTERN, text):
        findings["phone"] = re.findall(PHONE_PATTERN, text)

    return findings


def redact_pii(text: str) -> tuple[str, dict]:
    """Redact PII from text and return redacted text + findings."""
    findings = detect_pii(text)
    redacted = text

    # Redact SSN
    redacted = re.sub(SSN_PATTERN, "***-**-****", redacted)

    # Redact credit cards
    redacted = re.sub(CREDIT_CARD_PATTERN, "****-****-****-****", redacted)

    # Redact phone numbers (partially)
    redacted = re.sub(PHONE_PATTERN, "***-***-****", redacted)

    return redacted, findings


def process_patient_data(patient_id: str, notes: str, action_type: str) -> dict:
    """Process patient data through Faramesh with PII detection."""
    print(f"\n🏥 Processing patient {patient_id}")
    print(f"   Action: {action_type}")
    print(f"   Notes length: {len(notes)} chars")
    print()

    # Detect PII before submission
    pii_found = detect_pii(notes)

    if pii_found:
        print("  ⚠️  PII DETECTED before submission:")
        for pii_type, values in pii_found.items():
            print(f"     - {pii_type.upper()}: {len(values)} instance(s)")
        print()

        # Redact PII
        redacted_notes, _ = redact_pii(notes)
        print("  ✓ PII redacted before sending to Faramesh")
        print(f"    Original: '{notes[:50]}...'")
        print(f"    Redacted: '{redacted_notes[:50]}...'")
        print()

        notes_to_send = redacted_notes
        context_flags = {"pii_detected": True, "pii_redacted": True}
    else:
        print("  ✓ No PII detected")
        notes_to_send = notes
        context_flags = {"pii_detected": False}

    try:
        action = submit_action(
            agent_id=FARAMESH_AGENT_ID,
            tool="healthcare",
            operation=action_type,
            params={
                "patient_id": patient_id,
                "notes": notes_to_send,
                "action_type": action_type,
            },
            context={
                "agent_framework": "healthcare",
                "agent_role": "patient_data_processor",
                "compliance": "HIPAA",
                **context_flags,
            },
        )

        print(f"✓ Action submitted: {action['id']}")
        print(f"  Status: {action['status']}")
        print(f"  Decision: {action.get('decision', 'N/A')}")

        if pii_found:
            print("  🔒 PII Protection: Redacted data sent to Faramesh")
            print("     Original PII NEVER stored in audit trail")

        return {
            "success": True,
            "action_id": action["id"],
            "pii_detected": bool(pii_found),
            "pii_types": list(pii_found.keys()) if pii_found else [],
        }

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return {"success": False, "error": str(e)}


def run_demo():
    """Run the healthcare PII redaction demo."""
    if not ensure_server_available(FARAMESH_BASE_URL):
        return
    print("\n" + "=" * 80)
    print("🔒 Healthcare PII Redaction Demo")
    print("=" * 80)
    print()
    print("Scenario: Healthcare AI agent processes patient data")
    print("Risk: Agent might accidentally include SSN or other PII in logs")
    print("Protection: Faramesh detects and redacts PII before storage")
    print()
    print("Compliance: HIPAA, GDPR, CCPA")
    print()
    print("-" * 80)
    print()

    # Test cases
    test_cases = [
        {
            "patient_id": "PT-001",
            "notes": "Patient scheduled for follow-up appointment on Tuesday.",
            "action_type": "schedule_followup",
        },
        {
            "patient_id": "PT-002",
            "notes": "Patient SSN: 123-45-6789. Requires insurance verification.",
            "action_type": "verify_insurance",
        },
        {
            "patient_id": "PT-003",
            "notes": "Patient card ending in 4532-1234-5678-9012 on file. Call at 555-123-4567.",
            "action_type": "billing_update",
        },
        {
            "patient_id": "PT-004",
            "notes": "Emergency contact: 555-987-6543. Patient SSN 987-65-4321 for Medicare.",
            "action_type": "update_emergency_contact",
        },
    ]

    results = []

    for i, case in enumerate(test_cases, 1):
        print(f"📋 TEST CASE {i}/{len(test_cases)}")
        print("-" * 80)

        result = process_patient_data(**case)
        results.append({**case, **result})

    # Summary
    print("\n" + "=" * 80)
    print("✅ Demo Complete - Summary")
    print("=" * 80)
    print()

    pii_detected_count = sum(1 for r in results if r.get("pii_detected"))
    clean_count = len(results) - pii_detected_count

    print("Results:")
    print(f"  - Clean requests (no PII): {clean_count}")
    print(f"  - Requests with PII redacted: {pii_detected_count}")
    print()

    if pii_detected_count > 0:
        print("PII Types Detected:")
        all_pii_types = set()
        for r in results:
            if r.get("pii_types"):
                all_pii_types.update(r["pii_types"])

        for pii_type in sorted(all_pii_types):
            count = sum(1 for r in results if pii_type in r.get("pii_types", []))
            print(f"  - {pii_type.upper()}: {count} case(s)")

    print()
    print("Key Takeaways:")
    print("1. PII detected BEFORE sending to Faramesh")
    print("2. Sensitive data redacted automatically")
    print("3. Original PII NEVER stored in audit trail")
    print("4. Redacted version logged for debugging")
    print("5. Compliance-ready (HIPAA, GDPR, CCPA)")
    print()
    print("Protection Layers:")
    print("  Layer 1: Client-side PII detection (this demo)")
    print("  Layer 2: Server-side validation (Faramesh)")
    print("  Layer 3: Audit trail encryption")
    print("  Layer 4: Role-based access to logs")
    print()
    print("Real-World Impact:")
    print("  - Prevents HIPAA violations (up to $50,000 per violation)")
    print("  - Protects patient privacy")
    print("  - Enables safe AI usage in healthcare")
    print("  - Maintains compliance audit trail")
    print()


if __name__ == "__main__":
    run_demo()
