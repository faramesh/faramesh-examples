# 🎯 Faramesh Security Demo Suite

Complete end-to-end demos showcasing Faramesh's agent governance capabilities across multiple frameworks.

## 📁 Available Demos

### 1. Float Canonicalization (`05_float_canonicalization.py`)
**Framework:** Core
**Time:** 3 minutes
**Shows:** How 1.0, 1.00, and 1 produce identical SHA-256 hashes
**Why It Matters:** Foundation of deterministic policy enforcement

```bash
python 05_float_canonicalization.py
```

### 2. LangChain Delete-All Prevention (`01_langchain_delete_all.py`)
**Framework:** LangChain
**Time:** 5 minutes
**Shows:** Blocking dangerous `rm -rf /` commands while allowing safe operations
**Why It Matters:** Prevents catastrophic data loss from LLM hallucinations

```bash
python 01_langchain_delete_all.py
```

### 3. Customer Service Discount Control (`08_customer_service_discount.py`)
**Framework:** Business Logic
**Time:** 5 minutes
**Shows:** Preventing 100% discounts, requiring approval for 30-80%
**Why It Matters:** Based on real eBay/Artium case - saved $799.99 in demo alone

```bash
python 08_customer_service_discount.py
```

### 4. AutoGen High-Value Approval (`03_autogen_high_value_approval.py`)
**Framework:** AutoGen
**Time:** 5 minutes
**Shows:** Human-in-the-loop for transactions >= $1,000
**Why It Matters:** Prevents costly mistakes, maintains oversight

```bash
python 03_autogen_high_value_approval.py
```

### 5. MCP Filesystem Security (`04_mcp_filesystem_security.py`)
**Framework:** Model Context Protocol
**Time:** 5 minutes
**Shows:** Path-based access control, operation restrictions
**Why It Matters:** Secure MCP tool servers from unauthorized access

```bash
python 04_mcp_filesystem_security.py
```

### 6. CrewAI Infinite Loop Prevention (`02_crewai_infinite_loop.py`)
**Framework:** CrewAI
**Time:** 4 minutes
**Shows:** Rate limiting stops Agent A → Agent B → Agent A loops
**Why It Matters:** Prevents resource exhaustion and runaway costs

```bash
python 02_crewai_infinite_loop.py
```

### 7. Zero-Trust Cryptographic Audit (`06_zero_trust_crypto.py`)
**Framework:** Core
**Time:** 4 minutes
**Shows:** SHA-256 hashing, provenance IDs, immutable audit trail
**Why It Matters:** CISO-grade forensic investigation capability

```bash
python 06_zero_trust_crypto.py
```

### 8. Latency Benchmark (`07_latency_benchmark.py`)
**Framework:** Performance
**Time:** 3 minutes
**Shows:** Measuring <2ms overhead for local deployment
**Why It Matters:** Security doesn't mean slow

```bash
python 07_latency_benchmark.py
```

### 9. Healthcare PII Redaction (`09_healthcare_pii_redaction.py`)
**Framework:** Healthcare
**Time:** 4 minutes
**Shows:** Detecting and redacting SSN/credit cards from logs
**Why It Matters:** HIPAA compliance, avoid $50K penalties

```bash
python 09_healthcare_pii_redaction.py
```

### 10. DevOps Security (`10_devops_security.py`)
**Framework:** DevOps
**Time:** 5 minutes
**Shows:** Allow `ls` but block `rm -rf` - surgical command filtering
**Why It Matters:** Safe DevOps automation without system damage

```bash
python 10_devops_security.py
```

---

## 🚀 Quick Start

### Interactive Menu (Recommended)

```bash
python run_demos.py
```

This opens an interactive menu where you can:
- Run individual demos by number (1-10)
- Run all demos sequentially (`all`)
- Run 5-minute quick demo (`quick`)
- Run 40-minute full showcase (`full`)

### Run Individual Demo

```bash
python 01_langchain_delete_all.py
```

### Prerequisites

1. **Start Faramesh Server:**
```bash
cd ../faramesh-horizon-code
python -m faramesh.server.main
```

2. **Set Environment:**
```bash
export FARAMESH_URL="http://localhost:8000"
export FARAMESH_API_KEY="demo-api-key-123"
export OPENAI_API_KEY="your-key"  # For LangChain
```

3. **Install Dependencies:**
```bash
pip install langchain langchain-openai
pip install crewai  # Optional
pip install autogen  # Optional
```

---

## 📊 Demo Comparison

| Demo | Framework | Security Focus | Business Value |
|------|-----------|----------------|----------------|
| Float Canon | Core | Deterministic hashing | Foundation |
| LangChain | LangChain | Hallucination prevention | Data protection |
| Customer Service | Business | Discount limits | $799+ saved |
| AutoGen | AutoGen | Approval workflows | Cost control |
| MCP | MCP | Tool security | Access control |
| CrewAI | CrewAI | Loop prevention | Resource protection |
| Zero-Trust | Core | Audit trail | Compliance |
| Latency | Performance | Speed proof | Production-ready |
| Healthcare | Healthcare | PII protection | HIPAA compliance |
| DevOps | DevOps | Command filtering | System safety |

---

## 🎬 Presentation Tips

### For Technical Audiences
**Focus on:** Canonicalization, Zero-trust, Latency
**Deep dive:** Hash algorithms, policy DSL, SHA-256
**Show:** Server logs, policy evaluation, hash verification

### For Business Audiences
**Focus on:** Customer service, AutoGen, Healthcare
**Emphasize:** Cost savings, ROI, risk mitigation
**Show:** Dashboard, approval workflows, business impact

### For CISOs
**Focus on:** Zero-trust, Healthcare, DevOps
**Emphasize:** Audit trail, compliance, forensics
**Show:** Provenance IDs, governance reports, threat prevention

---

## 📝 Policy Files

Each demo has corresponding policy files in `../faramesh-horizon-code/profiles/`:

- `langchain_filesystem_policy.yaml` - LangChain security rules
- `crewai_rate_limit_policy.yaml` - Rate limiting configuration
- `autogen_financial_policy.yaml` - Financial approval thresholds
- `mcp_filesystem_policy.yaml` - Path-based access control
- `customer_service_policy.yaml` - Discount limit enforcement
- `devops_security_policy.yaml` - Command filtering rules

---

## 🔧 Troubleshooting

### Server Not Running
```bash
curl http://localhost:8000/health
# If fails, start: python -m faramesh.server.main
```

### Import Errors
```bash
export PYTHONPATH=/Users/xquark_home/Faramesh-Nexus:$PYTHONPATH
```

### Demos Fail
```bash
# Check logs
tail -f ../faramesh-horizon-code/server.log

# Verify SDK installed
pip install -e ../faramesh-python-sdk-code
```

---

## 📖 Full Documentation

- **[DEMO_SHOWCASE_GUIDE.md](../DEMO_SHOWCASE_GUIDE.md)** - Complete presentation guide
- **[DEMO_SETUP_COMPLETE.md](../DEMO_SETUP_COMPLETE.md)** - Setup summary
- **[README.md](../README.md)** - Project overview

---

## 🎯 Quick Demo Routes

**5-Minute Quick Demo:**
```bash
python run_demos.py
# Choose: 'quick'
# Runs: Canonicalization → LangChain → Customer Service
```

**Business-Focused Demo (15 min):**
1. Customer Service Discount (5 min)
2. AutoGen High-Value (5 min)
3. Healthcare PII (5 min)

**Technical Deep Dive (15 min):**
1. Float Canonicalization (3 min)
2. Zero-Trust Crypto (4 min)
3. Latency Benchmark (3 min)
4. DevOps Security (5 min)

**Full Showcase (40 min):**
```bash
python run_demos.py
# Choose: 'full'
# Runs all 10 demos sequentially
```

---

## ✅ What You'll Demonstrate

After running all demos, your audience will understand:

**Technical:**
- ✅ Deterministic hashing via canonicalization
- ✅ Policy-based governance at the execution gate
- ✅ Cryptographic audit trails with provenance IDs
- ✅ Sub-2ms latency overhead

**Business:**
- ✅ Real cost savings (prevented $799+ in losses)
- ✅ Risk mitigation (blocked system destruction)
- ✅ Compliance ready (HIPAA, GDPR, CCPA)
- ✅ Human-in-the-loop for critical decisions

**Security:**
- ✅ Zero-trust architecture
- ✅ Fail-closed enforcement
- ✅ Rate limiting and circuit breakers
- ✅ PII detection and redaction
- ✅ Surgical command filtering

---

**Status:** ✅ All 10 demos ready
**Total Runtime:** ~40 minutes (full showcase)
**Updated:** January 22, 2026
