# ARI Engine & RDI Monitor - System Architecture

**Status:** ✅ Complete
**Version:** 1.0.0
**Last Updated:** 2025-11-02

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Data Flow Diagram](#data-flow-diagram)
4. [Component Specifications](#component-specifications)
5. [Privacy Architecture](#privacy-architecture)
6. [Integration Points](#integration-points)
7. [API Reference](#api-reference)
8. [Usage Examples](#usage-examples)

---

## Overview

The ARI (Autonomy Retention Index) Engine and RDI (Reality Drift Index) Monitor form a comprehensive, privacy-first system for detecting AI-induced skill atrophy and epistemic drift.

### Key Features

**ARI Engine:**
- **Passive Lexical Analysis:** Continuous background measurement of user's writing complexity
- **Socratic Co-pilot:** Embedded interaction measurement through capability checkpoints
- **Deep Dive Mode:** Opt-in baseline establishment for gold-standard comparison

**RDI Monitor:**
- **Local-First Processing:** All analysis happens on-device
- **Privacy-First Governance:** Individual scores never exfiltrated
- **Aggregate-Only Sharing:** Minimum 100 users, explicit opt-in, complete anonymization

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          ADEM Platform                              │
│                 (Agency-Centric AI Framework)                       │
└────────────┬────────────────────────────────────┬───────────────────┘
             │                                    │
             │                                    │
    ┌────────▼───────────┐             ┌─────────▼──────────┐
    │                    │             │                    │
    │   ARI ENGINE       │             │   RDI MONITOR      │
    │   (On-Device)      │             │   (On-Device)      │
    │                    │             │   PRIVACY-FIRST    │
    └────────┬───────────┘             └─────────┬──────────┘
             │                                   │
    ┌────────┴──────────────┐          ┌────────┴─────────────┐
    │                       │          │                      │
┌───▼──────────┐  ┌────────▼─────┐  ┌─▼──────────┐  ┌──────▼────────┐
│   Passive    │  │   Socratic   │  │  Semantic  │  │   Consensus   │
│   Lexical    │  │   Co-pilot   │  │  Baseline  │  │    Model      │
│   Analyzer   │  │              │  │   (Local)  │  │   (Public)    │
│              │  │  Deep Dive   │  │            │  │               │
└──────┬───────┘  └──────┬───────┘  └─────┬──────┘  └───────┬───────┘
       │                 │                 │                 │
       │                 │                 │                 │
       └─────────┬───────┴─────────┬───────┴─────────────────┘
                 │                 │
         ┌───────▼─────────────────▼────────┐
         │                                  │
         │      Integration Layer           │
         │                                  │
         └──────┬────────────────┬──────────┘
                │                │
     ┌──────────▼─────┐  ┌──────▼──────────┐
     │  LLM Gateway   │  │  Agency         │
     │  (Socratic     │  │  Dashboard      │
     │   Questions)   │  │  (Private       │
     │                │  │   Metrics)      │
     └────────────────┘  └─────────────────┘
```

### Component Relationships

1. **ARI Engine** coordinates three measurement methods
2. **RDI Monitor** operates independently with strict privacy
3. Both integrate with **Agency Dashboard** for user awareness
4. **Socratic Co-pilot** uses **LLM Gateway** for question generation
5. All sensitive data stays **on-device**

---

## Data Flow Diagram

### ARI Engine Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                      USER INTERACTION                               │
│  (Writes text, delegates task, opts into deep dive)                │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
     ┌──────────▼──────────┐   ┌─────────▼────────────┐
     │ Passive Text Input  │   │ Task Delegation      │
     │ (Email, Code, Doc)  │   │ (User → AI)          │
     └──────────┬──────────┘   └─────────┬────────────┘
                │                        │
                │ [ON-DEVICE ANALYSIS]   │
                │ Raw text not stored    │
                │                        │
     ┌──────────▼──────────┐   ┌─────────▼────────────┐
     │ Lexical Metrics     │   │ UCC Questions        │
     │ • Diversity: 0.73   │   │ • "What should the   │
     │ • Complexity: 0.68  │   │    main logic be?"   │
     │ • Domain: 0.45      │   │                      │
     └──────────┬──────────┘   └─────────┬────────────┘
                │                        │
                │ [STORED LOCALLY]       │ [WAIT FOR USER]
                │ Only metrics, no text  │
                │                        │
     ┌──────────▼──────────┐   ┌─────────▼────────────┐
     │ Local Storage       │   │ User Response        │
     │ lexical_*.json      │   │ • Accurate           │
     │                     │   │ • Uncertain          │
     │ {                   │   │ • Delegated          │
     │   "diversity": 0.73,│   │                      │
     │   "complexity": 0.68│   └─────────┬────────────┘
     │   [NO RAW TEXT]     │             │
     │ }                   │             │
     └─────────────────────┘   ┌─────────▼────────────┐
                               │ Capability Score     │
                               │ • High: 0.9          │
                               │ • Low: 0.2           │
                               │ • Critical: 0.0      │
                               └─────────┬────────────┘
                                         │
                                         │ [STORED LOCALLY]
                                         │
                               ┌─────────▼────────────┐
                               │ Local Storage        │
                               │ ucc_*.json           │
                               │                      │
                               │ {                    │
                               │   "capability": 0.9, │
                               │   "ari_signal": "high"│
                               │   [NO RAW RESPONSE]  │
                               │ }                    │
                               └──────────────────────┘
```

### RDI Monitor Data Flow (Privacy-First)

```
┌─────────────────────────────────────────────────────────────────────┐
│                      USER INPUT                                     │
│  (Prompt, query, draft - analyzed but NEVER stored)                │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ [ON-DEVICE ONLY]
                             │
              ┌──────────────▼──────────────┐
              │                             │
              │   🔒 PRIVACY BOUNDARY 🔒    │
              │   ALL PROCESSING LOCAL      │
              │   NO EXFILTRATION           │
              │                             │
              └──────────────┬──────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
     ┌──────────▼──────────┐   ┌─────────▼────────────┐
     │ Semantic Analysis   │   │ Consensus Comparison │
     │ (Hash patterns only)│   │ (Public knowledge)   │
     │                     │   │                      │
     │ • Extract concepts  │   │ • Check against      │
     │ • Pattern signature │   │   common facts       │
     │ • NO STORAGE of raw │   │ • NO user data       │
     └──────────┬──────────┘   └─────────┬────────────┘
                │                        │
                │ [ANONYMIZE]            │ [AGGREGATE]
                │                        │
     ┌──────────▼──────────┐   ┌─────────▼────────────┐
     │ Local Baseline      │   │ Drift Signals        │
     │                     │   │                      │
     │ {                   │   │ {                    │
     │   "user_id": "a3f2",│   │   "type": "semantic",│
     │   [HASHED ID]       │   │   "magnitude": 0.3,  │
     │   "concepts": {     │   │   "pattern": "b4e9"  │
     │     "tech": 45,     │   │   [HASH, NOT TEXT]   │
     │     "impl": 32      │   │ }                    │
     │   }                 │   │                      │
     │   [NO RAW TEXT]     │   └─────────┬────────────┘
     │ }                   │             │
     └─────────────────────┘             │
                                         │
                               ┌─────────▼────────────┐
                               │ RDI Score (PRIVATE)  │
                               │                      │
                               │ • Overall: 0.25      │
                               │ • Level: MINOR_DRIFT │
                               │ • _is_private: TRUE  │
                               │                      │
                               │ [SHOWN TO USER ONLY] │
                               └─────────┬────────────┘
                                         │
                      ┌──────────────────┴──────────────────┐
                      │                                     │
          ┌───────────▼──────────┐            ┌────────────▼─────────┐
          │ Private Dashboard    │            │ Optional Aggregate   │
          │ (User sees own RDI)  │            │ (Explicit opt-in)    │
          │                      │            │                      │
          │ • Your RDI: 0.25     │            │ IF opt_in AND        │
          │ • Trend: stable      │            │ users >= 100 THEN:   │
          │ • Alerts: [private]  │            │                      │
          │                      │            │ {                    │
          │ [NO SHARING]         │            │   "avg": 0.28,       │
          └──────────────────────┘            │   "users": 150,      │
                                              │   [ANONYMIZED]       │
                                              │ }                    │
                                              └──────────────────────┘
```

### Privacy Boundary

```
╔═══════════════════════════════════════════════════════════════════╗
║                     🔒 ON-DEVICE BOUNDARY 🔒                     ║
║                                                                   ║
║  INSIDE (Local):                                                 ║
║  ✓ Raw user input analysis                                       ║
║  ✓ Individual RDI scores                                         ║
║  ✓ Semantic baselines                                            ║
║  ✓ User ID (hashed)                                              ║
║                                                                   ║
║  NEVER CROSSES BOUNDARY:                                         ║
║  ✗ Raw user text                                                 ║
║  ✗ Individual RDI scores                                         ║
║  ✗ Real user IDs                                                 ║
║  ✗ Personal data                                                 ║
║                                                                   ║
║  CAN CROSS (with opt-in):                                        ║
║  ✓ Anonymized aggregates (100+ users)                            ║
║  ✓ PII-scrubbed statistics                                       ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
```

---

## Component Specifications

### 1. PassiveLexicalAnalyzer

**Purpose:** Continuous background measurement of user's written output.

**Metrics Tracked:**
- Lexical diversity (type-token ratio)
- Vocabulary richness (unique words / total words)
- Syntactic complexity (sentence structure)
- Domain term density (technical vocabulary)

**Privacy:**
- ✅ Analyzes text locally
- ✅ Stores only aggregate metrics
- ✅ Raw text never stored
- ✅ Metrics stored locally as JSON

**API:**
```python
async def analyze_text(
    user_id: str,
    text: str,
    text_type: str = "document"
) -> LexicalMetrics
```

---

### 2. SocraticCopilot

**Purpose:** Embedded interaction measurement through Unassisted Capability Checkpoints (UCCs).

**UCC Types:**
- Accurate response → High ARI signal
- Partial response → Medium ARI signal
- Uncertain response → Low ARI signal
- Delegated response → Critical ARI signal

**Privacy:**
- ✅ Stores capability scores, not full responses
- ✅ Response text hashed before storage
- ✅ Local-only data

**API:**
```python
async def identify_uccs(
    user_id: str,
    task_description: str,
    domain: str
) -> List[str]

async def log_response(
    user_id: str,
    task_description: str,
    question: str,
    user_response: str,
    domain: str
) -> UnassistedCapabilityCheckpoint
```

---

### 3. DeepDiveMode

**Purpose:** Opt-in "Learn About Me" mode for establishing capability baselines.

**Features:**
- Domain-specific exploration questions
- Knowledge topic extraction
- Synthesis quality assessment
- Reasoning depth scoring

**Privacy:**
- ✅ User explicitly opts in
- ✅ Baseline stored locally
- ✅ No raw responses stored

**API:**
```python
async def start_deep_dive(
    user_id: str,
    domain: str
) -> List[str]

async def record_deep_dive_response(
    user_id: str,
    domain: str,
    question: str,
    response: str
) -> None

async def finalize_baseline(
    user_id: str,
    domain: str
) -> ARIBaseline
```

---

### 4. ARIEngine (Orchestrator)

**Purpose:** Coordinates all three ARI measurement methods.

**Calculates:**
- Lexical ARI (40% weight)
- Interaction ARI (40% weight)
- Baseline deviation (20% weight)

**Signal Levels:**
- **HIGH:** ≥ 0.75 - User demonstrating strong capability
- **MEDIUM:** 0.5-0.74 - Moderate capability
- **LOW:** 0.25-0.49 - Reduced capability
- **CRITICAL:** < 0.25 - Severe capability loss

**API:**
```python
def calculate_comprehensive_ari(
    user_id: str,
    domain: Optional[str] = None
) -> ARIScore
```

---

### 5. RDIMonitor

**Purpose:** Privacy-first reality drift detection.

**Drift Types:**
- Semantic drift (concept usage changes)
- Factual drift (divergence from consensus facts)
- Logical drift (reasoning pattern changes)

**Privacy Guarantees:**
1. ✅ **Local-First:** All processing on-device
2. ✅ **User ID Hashing:** Real IDs never stored
3. ✅ **No Raw Storage:** Only aggregate patterns
4. ✅ **Private Scores:** Shown only to user
5. ✅ **Opt-In Aggregates:** Explicit consent required
6. ✅ **100+ User Threshold:** Anonymization requirement

**API:**
```python
async def analyze_input(
    user_id: str,
    user_input: str,
    domain: Optional[str] = None
) -> Tuple[float, List[DriftSignal]]

def calculate_rdi_score(
    user_id: str,
    lookback_days: int = 30
) -> RDIScore  # Marked as _is_private=True

def get_user_rdi_for_dashboard(
    user_id: str
) -> Dict[str, Any]  # Private, for user only

def opt_in_to_aggregate_sharing(
    user_id: str
) -> bool

def generate_anonymized_aggregate(
) -> Optional[AnonymizedRDIStats]  # Only if >= 100 users
```

---

## Privacy Architecture

### RDI Privacy Layers

```
Layer 1: Input Processing
├─ Raw input analyzed locally
├─ Pattern extraction only
└─ Raw text discarded immediately

Layer 2: Storage
├─ User IDs hashed (SHA-256)
├─ Patterns stored as signatures (hashed)
└─ No PII in storage

Layer 3: Scoring
├─ Individual scores calculated locally
├─ Marked as _is_private=True
└─ Never transmitted

Layer 4: Display
├─ User sees own score on private dashboard
├─ No sharing with platform or others
└─ Privacy notice displayed

Layer 5: Aggregation (Optional)
├─ Requires explicit user opt-in
├─ Minimum 100 users threshold
├─ Complete anonymization applied
└─ PII scrubbing verified
```

### Privacy Verification

**Verification Checklist:**
- [ ] Raw user input never stored? ✅
- [ ] User IDs hashed? ✅
- [ ] Individual scores stay local? ✅
- [ ] Aggregates require 100+ users? ✅
- [ ] Explicit opt-in for sharing? ✅
- [ ] PII scrubbed from aggregates? ✅
- [ ] Privacy markers in code? ✅
- [ ] On-device processing only? ✅

---

## Integration Points

### 1. Agency Dashboard Integration

**Display for ARI:**
```python
# In agency_dashboard.py

from ai_pal.monitoring.ari_engine import ARIEngine

ari_engine = ARIEngine(storage_dir="./data/ari")

# Get ARI for dashboard
ari_score = ari_engine.calculate_comprehensive_ari(user_id, domain)

dashboard_data = {
    "ari": {
        "overall": ari_score.overall_ari,
        "level": ari_score.signal_level.value,
        "lexical": ari_score.lexical_ari,
        "interaction": ari_score.interaction_ari,
        "trend": ari_score.trend_direction,
        "alerts": ari_score.alerts
    }
}
```

**Display for RDI (Private):**
```python
# In agency_dashboard.py

from ai_pal.monitoring.rdi_monitor import RDIMonitor

rdi_monitor = RDIMonitor(storage_dir="./data/rdi", enable_privacy_mode=True)

# Get RDI for user's PRIVATE dashboard
rdi_data = rdi_monitor.get_user_rdi_for_dashboard(user_id)

dashboard_data = {
    "rdi": rdi_data,
    # Includes privacy notice
}
```

### 2. LLM Gateway Integration

**Socratic Co-pilot Questions:**
```python
# In integrated_system.py or llm gateway

from ai_pal.monitoring.ari_engine import ARIEngine

ari_engine = ARIEngine(storage_dir="./data/ari")

# When user delegates a task
async def on_task_delegation(user_id, task_description, domain):
    # Generate Socratic questions
    questions = await ari_engine.intercept_task_delegation(
        user_id, task_description, domain
    )

    # Present questions to user via LLM
    for question in questions:
        response = await prompt_user(question)
        await ari_engine.record_ucc_response(
            user_id, task_description, question, response, domain
        )
```

### 3. Passive Text Analysis Integration

**Background Analysis:**
```python
# In text processing pipeline

from ai_pal.monitoring.ari_engine import ARIEngine

ari_engine = ARIEngine(storage_dir="./data/ari")

# Analyze user's written output
async def on_user_text_input(user_id, text, text_type):
    # Passive analysis (non-invasive)
    metrics = await ari_engine.analyze_user_text(user_id, text, text_type)

    # Metrics stored, raw text discarded
    # User not interrupted
```

---

## API Reference

### ARIEngine

```python
class ARIEngine:
    def __init__(
        self,
        storage_dir: Path,
        lexical_lookback_days: int = 30,
        interaction_lookback_days: int = 30
    )

    async def analyze_user_text(
        self,
        user_id: str,
        text: str,
        text_type: str = "document"
    ) -> LexicalMetrics

    async def intercept_task_delegation(
        self,
        user_id: str,
        task_description: str,
        domain: str
    ) -> List[str]

    async def record_ucc_response(
        self,
        user_id: str,
        task_description: str,
        question: str,
        response: str,
        domain: str
    ) -> UnassistedCapabilityCheckpoint

    async def start_deep_dive_session(
        self,
        user_id: str,
        domain: str
    ) -> List[str]

    async def record_deep_dive_response(
        self,
        user_id: str,
        domain: str,
        question: str,
        response: str
    ) -> None

    async def finalize_deep_dive_baseline(
        self,
        user_id: str,
        domain: str
    ) -> ARIBaseline

    def calculate_comprehensive_ari(
        self,
        user_id: str,
        domain: Optional[str] = None
    ) -> ARIScore

    def get_ari_history(
        self,
        user_id: str,
        days: int = 90
    ) -> List[ARIScore]
```

### RDIMonitor

```python
class RDIMonitor:
    def __init__(
        self,
        storage_dir: Path,
        enable_privacy_mode: bool = True,  # Should always be True
        consensus_model_path: Optional[Path] = None
    )

    async def analyze_input(
        self,
        user_id: str,
        user_input: str,
        domain: Optional[str] = None
    ) -> Tuple[float, List[DriftSignal]]

    def calculate_rdi_score(
        self,
        user_id: str,
        lookback_days: int = 30
    ) -> RDIScore  # _is_private=True

    def get_user_rdi_for_dashboard(
        self,
        user_id: str
    ) -> Dict[str, Any]  # Private, for user only

    def opt_in_to_aggregate_sharing(
        self,
        user_id: str
    ) -> bool

    def generate_anonymized_aggregate(
        self
    ) -> Optional[AnonymizedRDIStats]  # >= 100 users required
```

---

## Usage Examples

### Example 1: Basic ARI Measurement

```python
from pathlib import Path
from ai_pal.monitoring.ari_engine import ARIEngine

# Initialize
ari_engine = ARIEngine(storage_dir=Path("./data/ari"))

# Passive text analysis
text = "The implementation requires careful algorithmic consideration..."
metrics = await ari_engine.analyze_user_text(
    user_id="user123",
    text=text,
    text_type="code"
)

# Calculate ARI
ari_score = ari_engine.calculate_comprehensive_ari("user123")
print(f"ARI: {ari_score.overall_ari:.3f} ({ari_score.signal_level.value})")
```

### Example 2: Socratic Co-pilot

```python
# User delegates a task
task = "Write a function to sort an array"

# Generate questions
questions = await ari_engine.intercept_task_delegation(
    user_id="user123",
    task_description=task,
    domain="programming"
)

# Ask user
for question in questions:
    user_response = input(f"{question}\n> ")

    await ari_engine.record_ucc_response(
        user_id="user123",
        task_description=task,
        question=question,
        response=user_response,
        domain="programming"
    )
```

### Example 3: Deep Dive Mode

```python
# User opts into deep dive
domain = "programming"

questions = await ari_engine.start_deep_dive_session("user123", domain)

for question in questions:
    response = input(f"{question}\n> ")
    await ari_engine.record_deep_dive_response("user123", domain, question, response)

# Finalize baseline
baseline = await ari_engine.finalize_deep_dive_baseline("user123", domain)
print(f"Baseline established: {baseline.sample_count} samples")
```

### Example 4: RDI Monitoring (Privacy-First)

```python
from pathlib import Path
from ai_pal.monitoring.rdi_monitor import RDIMonitor

# Initialize with privacy mode
rdi_monitor = RDIMonitor(
    storage_dir=Path("./data/rdi"),
    enable_privacy_mode=True  # Always True in production
)

# Analyze user input (local only, not stored)
user_input = "The earth orbits the sun..."
drift_score, signals = await rdi_monitor.analyze_input(
    user_id="user123",
    user_input=user_input,
    domain="science"
)

# Calculate RDI score (private)
rdi_score = rdi_monitor.calculate_rdi_score("user123")

# Get for private dashboard (shown to user only)
dashboard_data = rdi_monitor.get_user_rdi_for_dashboard("user123")
print(f"Your RDI: {dashboard_data['current_rdi']:.3f}")
print(f"Privacy: {dashboard_data['_privacy_notice']}")
```

### Example 5: Optional Aggregate Sharing

```python
# User opts in
rdi_monitor.opt_in_to_aggregate_sharing("user123")

# Platform attempts to generate aggregate
# (Will only succeed if >= 100 users opted in)
aggregate = rdi_monitor.generate_anonymized_aggregate()

if aggregate:
    print(f"Aggregate from {aggregate.total_users} users")
    print(f"Average RDI: {aggregate.average_rdi:.3f}")
    print(f"Anonymized: {aggregate.anonymization_applied}")
    print(f"PII scrubbed: {aggregate.pii_scrubbed}")
else:
    print("Insufficient users for privacy-preserving aggregate")
```

---

## Security & Privacy Considerations

### Data Storage

**ARI Engine:**
- Metrics stored as JSON in local storage
- No cloud sync
- User can delete at any time
- File naming: `lexical_<user_id>_<timestamp>.json`

**RDI Monitor:**
- User IDs hashed before storage
- No raw input text stored
- Local-only storage
- File naming: `rdi_baseline_<hashed_id>.json`

### Privacy Compliance

- ✅ GDPR compliant (user data ownership)
- ✅ No telemetry without opt-in
- ✅ Right to deletion (user can clear local data)
- ✅ Transparency (privacy notices displayed)
- ✅ Minimum aggregation (100+ users)

---

## Troubleshooting

**Q: ARI scores seem unstable?**

A: Ensure sufficient samples:
- Minimum 10 text samples for lexical ARI
- Minimum 5 UCC responses for interaction ARI
- Deep dive baseline recommended for stability

**Q: RDI not calculating?**

A: Check:
- Privacy mode enabled (should be True)
- Sufficient input samples (5+)
- Storage directory exists and writable

**Q: Can't generate aggregate?**

A: Requirements:
- Minimum 100 users opted in
- Each user must have RDI score
- Privacy thresholds must be met

---

## Future Enhancements

### Planned Features

1. **ARI Engine:**
   - ML-based trend prediction
   - Custom domain baselines
   - Collaborative baselines (opt-in)

2. **RDI Monitor:**
   - Advanced NLP for drift detection
   - Multi-language support
   - Improved consensus models

3. **Integration:**
   - Real-time dashboard updates
   - Alert system for critical drift
   - Export capabilities (anonymized)

---

**Last Updated:** 2025-11-02
**Version:** 1.0.0
**Status:** Production Ready
**Privacy Audit:** Passed ✅