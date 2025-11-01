# AI-PAL 4-Gate System - Pre-Commit Hooks

This directory contains pre-commit hooks that enforce the AI-PAL 4-Gate System before allowing commits.

## The 4 Gates

### Gate 1: Net Agency
Ensures that AI assistance enhances rather than reduces user capability. Checks that:
- New AI features include skill development scaffolding
- ARI monitoring is in place for autonomous features
- Bottleneck detection and resolution are available

### Gate 2: Extraction Static Analysis
Prevents dark patterns and exploitative design. Checks for:
- Automatic subscriptions
- Hidden costs
- Forced continuity
- Difficult cancellation processes
- Privacy violations

### Gate 3: Humanity Override
Ensures users maintain control. Validates:
- All autonomous features have stop/cancel mechanisms
- User confirmation for critical actions
- Override capabilities are easily accessible
- No forced automation

### Gate 4: Performance Parity
Ensures AI assistance doesn't slow down workflows. Checks:
- Response times meet thresholds
- No blocking synchronous operations in async code
- Efficient algorithms (no excessive nested loops)
- Resource usage is reasonable

## Installation

To install the pre-commit hooks:

```bash
cd /path/to/ai-pal
./scripts/gates/install_hooks.sh
```

This will:
1. Create a pre-commit hook in `.git/hooks/`
2. Make the gate check script executable
3. Configure automatic gate validation

## Usage

### Normal Commits
Gates run automatically:

```bash
git add .
git commit -m "Your commit message"
# Gates run automatically before commit
```

### Testing Hooks
Test without making changes:

```bash
git commit --allow-empty -m "Test gates"
```

### Bypassing Hooks (Not Recommended)
In emergencies only:

```bash
git commit --no-verify -m "Emergency commit"
```

**Warning**: Bypassing gates defeats the purpose of agency retention and should only be done in exceptional circumstances.

## Gate Check Output

When you commit, you'll see output like:

```
============================================================
Running Pre-Commit Gate Checks
============================================================

Gate 1: Net Agency...
  ✓ PASSED
    ai_features_added: 2
    scaffolding_added: 2

Gate 2: Extraction Static Analysis...
  ✓ PASSED
    files_checked: 5
    dark_patterns_found: 0

Gate 3: Humanity Override...
  ✓ PASSED
    files_checked: 5

Gate 4: Performance Parity...
  ✓ PASSED
    files_checked: 5

============================================================
✓ ALL GATES PASSED - Commit allowed
============================================================
```

If a gate fails:

```
============================================================
Running Pre-Commit Gate Checks
============================================================

Gate 1: Net Agency...
  ✗ FAILED: Adding AI features without skill development scaffolding
    ai_features_added: 3
    scaffolding_added: 0

...

============================================================
✗ ONE OR MORE GATES FAILED - Commit blocked
============================================================

To bypass gate checks (not recommended):
  git commit --no-verify
```

## Customization

### Adjusting Gate Sensitivity

Edit `pre_commit_gate_check.py` to customize gate thresholds:

```python
# Example: Adjust AI feature threshold in Gate 1
if ai_additions > 5 and scaffolding_additions == 0:  # Increased from default
    return {"passed": False, ...}
```

### Adding Custom Checks

Add your own checks by extending the gate methods:

```python
async def _run_gate1(self, gate: AgencyValidator) -> Dict[str, Any]:
    # Your custom checks here
    my_check_result = self._my_custom_check()

    if not my_check_result:
        return {"passed": False, "reason": "Custom check failed"}

    # Original checks
    ...
```

### Disabling Specific Gates

Comment out gates in `run_all_gates()`:

```python
self.gates = {
    "Gate 1: Net Agency": AgencyValidator(),
    "Gate 2: Extraction Static Analysis": ExtractionAnalyzer(),
    # "Gate 3: Humanity Override": OverrideChecker(),  # Disabled
    "Gate 4: Performance Parity": PerformanceValidator(),
}
```

## Troubleshooting

### Hook Not Running

Check that the hook is installed:
```bash
ls -la .git/hooks/pre-commit
```

If missing, reinstall:
```bash
./scripts/gates/install_hooks.sh
```

### Permission Errors

Make scripts executable:
```bash
chmod +x scripts/gates/*.sh scripts/gates/*.py
```

### Python Not Found

Ensure Python 3 is in your PATH:
```bash
which python3
```

Or edit the hook to use your Python:
```bash
# In .git/hooks/pre-commit
/path/to/your/python3 "${PROJECT_ROOT}/scripts/gates/pre_commit_gate_check.py"
```

### Module Import Errors

Ensure AI-PAL is properly installed:
```bash
pip install -e .
```

## Uninstallation

To remove the hooks:

```bash
rm .git/hooks/pre-commit
```

## CI/CD Integration

For automated gate checking in CI/CD pipelines, see:
- `.github/workflows/gate_validation.yml` - GitHub Actions workflow
- Documentation in `docs/CI_CD_GATES.md`

## Philosophy

The 4-Gate System embodies the core principles of AI-PAL:

1. **Agency Retention**: Users should grow more capable, not less
2. **Ethical Design**: No dark patterns or exploitation
3. **User Sovereignty**: Ultimate control remains with humans
4. **Performance**: AI should accelerate, not hinder

By enforcing these gates at commit time, we ensure every code change aligns with these principles.

## Further Reading

- Main documentation: `docs/GATES_OVERVIEW.md`
- Phase 1 specification: `docs/PHASE1_FULL_SPECIFICATION.md`
- Agency Retention Index: `docs/ARI_DESIGN.md`
- Epistemic Debt Management: `docs/EDM_DESIGN.md`
