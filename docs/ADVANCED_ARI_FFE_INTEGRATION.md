# Advanced ARI-FFE Integration

**Status:** ✅ Complete (as of 2025-10-26)

## Overview

The Advanced ARI-FFE Integration connects the Agency Retention Index (ARI) monitoring system with the Fractal Flow Engine (FFE) to provide:

1. **Real-time bottleneck detection** from ARI snapshots
2. **Adaptive difficulty scaling** based on user performance
3. **Proactive skill atrophy prevention** before skills decline

This integration enables the FFE to automatically respond to user agency patterns, adjusting task difficulty and preventing skill loss before it becomes critical.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    ARI Monitor                          │
│  - Records AgencySnapshot for each task                │
│  - Tracks: skill_development, ai_reliance, agency      │
└────────────────┬────────────────────────────────────────┘
                 │
                 │ Real-time monitoring
                 │
        ┌────────▼────────┐
        │                 │
        │  Advanced       │
        │  Integration    │
        │  Systems        │
        │                 │
        └─┬───────┬───────┬─┘
          │       │       │
    ┌─────▼──┐ ┌─▼─────┐ ┌▼──────────┐
    │ Real   │ │Adaptive│ │  Skill    │
    │ Time   │ │Difficul│ │ Atrophy   │
    │Bottlenk│ │  ty    │ │Prevention │
    │Detector│ │Scaler  │ │           │
    └───┬────┘ └───┬────┘ └─────┬─────┘
        │          │            │
        │    ┌─────▼────────────▼─────┐
        └────►   Growth Scaffold       │
             │  (Bottleneck Queue)     │
             └──────────┬──────────────┘
                        │
                   ┌────▼─────────┐
                   │ Strength     │
                   │ Amplifier    │
                   │ (Reframing)  │
                   └──────────────┘
```

---

## Components

### 1. RealTimeBottleneckDetector

**Purpose:** Monitors ARI snapshots in real-time and automatically creates bottleneck tasks when thresholds are exceeded.

**Key Features:**
- Real-time snapshot analysis
- Three detection triggers:
  - Skill loss: `skill_development < -0.15`
  - Agency loss: `delta_agency < -0.1`
  - High AI reliance: `ai_reliance > 0.9`
- Severity scoring for prioritization
- Duplicate prevention
- Auto-queueing to Growth Scaffold

**Usage Example:**

```python
from ai_pal.monitoring.ari_monitor import ARIMonitor
from ai_pal.ffe.components.growth_scaffold import GrowthScaffold
from ai_pal.ffe.integration import RealTimeBottleneckDetector

# Initialize components
ari_monitor = ARIMonitor(storage_dir="./data/ari")
growth_scaffold = GrowthScaffold()

# Create detector
detector = RealTimeBottleneckDetector(
    ari_monitor=ari_monitor,
    growth_scaffold=growth_scaffold,
    skill_loss_threshold=-0.15,
    agency_loss_threshold=-0.1,
    high_reliance_threshold=0.9,
)

# Analyze snapshot (call this after each ARI snapshot is recorded)
bottleneck = await detector.analyze_snapshot(snapshot)

if bottleneck:
    print(f"Bottleneck detected: {bottleneck.task_category}")
    print(f"Severity: {bottleneck.skill_gap_severity:.2f}")
    print(f"Reason: {bottleneck.bottleneck_reason}")
```

**Severity Calculation:**

The detector calculates severity as a weighted combination:
- 40% skill gap (how far below ideal skill level)
- 30% avoidance frequency (inferred from AI reliance + low autonomy)
- 20% agency impact (magnitude of agency loss)
- 10% time since last attempt

Urgency levels:
- **Critical:** severity ≥ 0.8
- **High:** severity ≥ 0.6
- **Medium:** severity ≥ 0.4
- **Low:** severity < 0.4

---

### 2. AdaptiveDifficultyScaler

**Purpose:** Calculates optimal task difficulty based on user's ARI performance trends.

**Key Features:**
- "Goldilocks zone" difficulty calculation
- Performance score from 4 metrics:
  - Skill development trend (30%)
  - AI reliance (30%)
  - Autonomy retention (20%)
  - Agency change (20%)
- Adaptive recommendations:
  - Complexity level (easy/comfortable/moderate/challenging)
  - Time block size (tiny/small/medium/large)
  - Growth vs comfort task ratio
- Category-specific difficulty adjustment

**Usage Example:**

```python
from ai_pal.ffe.integration import AdaptiveDifficultyScaler

# Create scaler
scaler = AdaptiveDifficultyScaler(
    ari_monitor=ari_monitor,
    lookback_days=14,  # Analyze last 14 days
)

# Calculate optimal difficulty
difficulty = await scaler.calculate_optimal_difficulty(
    user_id="user123",
    task_category="coding"  # Optional: category-specific
)

print(f"Performance score: {difficulty['performance_score']:.2f}")
print(f"Complexity: {difficulty['complexity']}")
print(f"Time block size: {difficulty['time_block_size']}")
print(f"Growth tasks: {difficulty['growth_task_ratio']:.0%}")
print(f"Recommendation: {difficulty['recommendation']}")
```

**Performance Tiers:**

| Performance Score | Complexity | Time Block | Growth Ratio |
|-------------------|------------|------------|--------------|
| ≥ 0.75 | Challenging | Large (90 min) | 45-50% |
| 0.55 - 0.74 | Moderate | Medium (45 min) | 30-45% |
| 0.35 - 0.54 | Comfortable | Small (25 min) | 20-30% |
| < 0.35 | Easy | Tiny (15 min) | 10-20% |

---

### 3. SkillAtrophyPrevention

**Purpose:** Proactively detects declining skills and suggests practice tasks before significant atrophy.

**Key Features:**
- Early warning system (14 days unused)
- Critical alerts (30 days unused)
- Skill decline trend detection
- Practice urgency scoring
- Auto-generated practice suggestions
- Skill trend visualization data

**Usage Example:**

```python
from ai_pal.ffe.integration import SkillAtrophyPrevention

# Create prevention system
prevention = SkillAtrophyPrevention(
    ari_monitor=ari_monitor,
    growth_scaffold=growth_scaffold,
    warning_days=14,
    critical_days=30,
)

# Detect declining skills
declining = await prevention.detect_declining_skills(user_id="user123")

for skill in declining:
    print(f"Skill: {skill['skill_category']}")
    print(f"Days since use: {skill['days_since_use']}")
    print(f"Status: {skill['status']}")
    print(f"Practice urgency: {skill['practice_urgency']:.2f}")

# Generate practice suggestions
suggestions = await prevention.generate_practice_suggestions(
    user_id="user123",
    max_suggestions=3
)

for suggestion in suggestions:
    print(f"Suggested task: {suggestion['suggested_task']}")
    print(f"Rationale: {suggestion['rationale']}")

# Auto-queue practice tasks
queued_tasks = await prevention.queue_practice_tasks(
    user_id="user123",
    max_tasks=2
)

print(f"Queued {len(queued_tasks)} practice tasks")
```

**Practice Urgency Formula:**

Urgency = 0.4 × time_urgency + 0.4 × decline_urgency + 0.2 × level_urgency

Where:
- **Time urgency:** Days unused / critical_days (max 1.0)
- **Decline urgency:** Rate of skill decline (max 1.0)
- **Level urgency:** Current skill level (losing high-level skills is worse)

---

## Integration Workflow

### Complete Integration Example

```python
from ai_pal.monitoring.ari_monitor import ARIMonitor, AgencySnapshot
from ai_pal.ffe.components.growth_scaffold import GrowthScaffold
from ai_pal.ffe.integration import (
    RealTimeBottleneckDetector,
    AdaptiveDifficultyScaler,
    SkillAtrophyPrevention,
)

# Initialize core systems
ari_monitor = ARIMonitor(storage_dir="./data/ari")
growth_scaffold = GrowthScaffold()

# Initialize advanced integration systems
detector = RealTimeBottleneckDetector(
    ari_monitor=ari_monitor,
    growth_scaffold=growth_scaffold,
)

scaler = AdaptiveDifficultyScaler(
    ari_monitor=ari_monitor,
    lookback_days=14,
)

prevention = SkillAtrophyPrevention(
    ari_monitor=ari_monitor,
    growth_scaffold=growth_scaffold,
)

# User completes a task
async def on_task_complete(user_id: str, task_result):
    # Record ARI snapshot
    snapshot = AgencySnapshot(
        timestamp=datetime.now(),
        task_id=task_result["id"],
        task_type=task_result["type"],
        delta_agency=task_result["agency_change"],
        skill_development=task_result["skill_delta"],
        ai_reliance=task_result["ai_reliance"],
        # ... other metrics
    )

    await ari_monitor.record_snapshot(snapshot)

    # Real-time bottleneck detection
    bottleneck = await detector.analyze_snapshot(snapshot)
    if bottleneck:
        print(f"⚠️  Bottleneck detected: {bottleneck.task_category}")

    # Get difficulty recommendation for next task
    difficulty = await scaler.calculate_optimal_difficulty(user_id)
    print(f"📊 Recommended difficulty: {difficulty['complexity']}")

    # Check for skill atrophy (periodic, e.g., daily)
    if should_check_atrophy():
        suggestions = await prevention.generate_practice_suggestions(user_id)
        if suggestions:
            print(f"💡 {len(suggestions)} practice suggestions available")

# Periodic skill atrophy check (run daily)
async def daily_skill_check(user_id: str):
    # Queue practice tasks for declining skills
    queued = await prevention.queue_practice_tasks(user_id, max_tasks=2)

    if queued:
        print(f"🎯 Queued {len(queued)} practice tasks")
        for task in queued:
            print(f"  - {task.task_category} (urgency: {task.importance_score:.2f})")
```

---

## Configuration

### Threshold Tuning

**RealTimeBottleneckDetector:**

```python
detector = RealTimeBottleneckDetector(
    ari_monitor=ari_monitor,
    growth_scaffold=growth_scaffold,

    # Adjust these based on user tolerance
    skill_loss_threshold=-0.15,      # More negative = less sensitive
    agency_loss_threshold=-0.1,      # More negative = less sensitive
    high_reliance_threshold=0.9,     # Higher = less sensitive
)
```

**AdaptiveDifficultyScaler:**

```python
scaler = AdaptiveDifficultyScaler(
    ari_monitor=ari_monitor,
    lookback_days=14,  # Increase for more stable recommendations
)
```

**SkillAtrophyPrevention:**

```python
prevention = SkillAtrophyPrevention(
    ari_monitor=ari_monitor,
    growth_scaffold=growth_scaffold,
    warning_days=14,    # First warning threshold
    critical_days=30,   # Critical atrophy threshold
)
```

---

## Testing

Comprehensive tests are available in `tests/integration/test_advanced_ari_ffe_integration.py`:

```bash
# Run all advanced integration tests
pytest tests/integration/test_advanced_ari_ffe_integration.py -v

# Run specific test
pytest tests/integration/test_advanced_ari_ffe_integration.py::test_real_time_detector_skill_loss -v

# Run full workflow test
pytest tests/integration/test_advanced_ari_ffe_integration.py::test_full_integration_workflow -v
```

**Test Coverage:**
- ✅ Real-time bottleneck detection (7 tests)
- ✅ Adaptive difficulty scaling (5 tests)
- ✅ Skill atrophy prevention (8 tests)
- ✅ Full integration workflow (1 test)

---

## Performance Considerations

### Efficiency

- **RealTimeBottleneckDetector:** O(1) per snapshot analysis
- **AdaptiveDifficultyScaler:** O(n) where n = snapshots in lookback period (typically ~100-200)
- **SkillAtrophyPrevention:** O(m × k) where m = unique task types, k = snapshots per type

### Memory Usage

All systems use in-memory caching from ARIMonitor. For large-scale deployments:
- Consider periodic cache pruning (keep last 90 days)
- Use database storage for historical data
- Implement lazy loading for skill trends

### Recommended Frequencies

- **Bottleneck detection:** Every snapshot (real-time)
- **Difficulty scaling:** Before each task planning session
- **Atrophy prevention:** Daily or weekly batch job

---

## Future Enhancements

### Planned Features

1. **Background Monitoring**
   - Async background task to monitor ARI continuously
   - WebSocket notifications for real-time alerts

2. **Machine Learning Integration**
   - Predict skill atrophy before it occurs
   - Personalized threshold tuning
   - Optimal difficulty prediction

3. **Dashboard Integration**
   - Skill trend visualizations
   - Bottleneck history graphs
   - Difficulty adjustment recommendations

4. **Multi-User Analytics**
   - Aggregate trends across users
   - Benchmark difficulty settings
   - Best practices discovery

---

## Troubleshooting

### Common Issues

**Q: Bottlenecks not being detected?**

A: Check that:
1. ARI snapshots are being recorded correctly
2. Thresholds aren't too lenient (e.g., `-0.15` might be too strict)
3. `analyze_snapshot()` is being called after each snapshot

**Q: Difficulty recommendations seem off?**

A: Ensure:
1. Sufficient historical data (minimum 5-10 snapshots)
2. `lookback_days` isn't too short (recommended: 14 days)
3. ARI metrics are calculated correctly

**Q: Practice tasks not appearing?**

A: Verify:
1. Skills have actually been unused for warning_days+
2. `detect_declining_skills()` returns results
3. Growth Scaffold is properly initialized

---

## API Reference

### RealTimeBottleneckDetector

```python
async def analyze_snapshot(snapshot: AgencySnapshot) -> Optional[BottleneckTask]
```
Analyze snapshot and create bottleneck if thresholds exceeded.

```python
def reset_created_bottlenecks(user_id: Optional[str] = None) -> None
```
Reset tracking of created bottlenecks (for testing or fresh start).

### AdaptiveDifficultyScaler

```python
async def calculate_optimal_difficulty(
    user_id: str,
    task_category: Optional[str] = None
) -> Dict[str, Any]
```
Calculate optimal difficulty for user (optionally category-specific).

Returns:
```python
{
    "performance_score": float,  # 0-1
    "complexity": str,  # "easy"/"comfortable"/"moderate"/"challenging"
    "complexity_level": int,  # 1-4
    "time_block_size": TimeBlockSize,
    "growth_task_ratio": float,  # 0-1
    "comfort_task_ratio": float,  # 0-1
    "recommendation": str,  # Human-readable
}
```

### SkillAtrophyPrevention

```python
async def detect_declining_skills(user_id: str) -> List[Dict[str, Any]]
```
Detect skills showing decline trends.

```python
async def generate_practice_suggestions(
    user_id: str,
    max_suggestions: int = 3
) -> List[Dict[str, Any]]
```
Generate practice task suggestions for declining skills.

```python
async def queue_practice_tasks(
    user_id: str,
    max_tasks: int = 2
) -> List[BottleneckTask]
```
Queue practice tasks to Growth Scaffold.

```python
async def get_skill_trends(
    user_id: str,
    task_category: str
) -> Dict[str, Any]
```
Get skill trend data for visualization.

---

## Contributing

See the main [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

When contributing to advanced integration:
- Maintain backward compatibility with ARIConnector
- Add tests for any new detection logic
- Update this documentation
- Consider performance impact

---

## License

See [LICENSE](../LICENSE)

---

**Last Updated:** 2025-10-26
**Version:** 1.0.0
**Status:** Production Ready
