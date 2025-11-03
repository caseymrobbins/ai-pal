# AI Self-Improvement Patch Request System

## Overview

The AI Self-Improvement Patch Request System allows the AI to propose code modifications to improve its own functionality, while maintaining **strict human oversight** through a multi-layered approval process. This ensures the AI can evolve and improve based on real-world feedback, but cannot modify its core ethical constraints or bypass safety mechanisms.

## Architecture

### Components

1. **The "Will": Self-Improvement Loop** (`src/ai_pal/improvement/self_improvement.py`)
   - Analyzes performance feedback from multiple sources
   - Uses local model to research optimal coding patterns
   - Generates "Patch Request" objects containing:
     - `target_file`: File to modify
     - `reasoning`: Natural language explanation
     - `diff`: Git-style diff of changes
     - `new_code_blob`: Complete new file content
     - `confidence`: AI's confidence score (0-1)

2. **The "Ethical Review": Gate System** (`src/ai_pal/gates/gate_system.py`)
   - Validates patch requests against protected kernel files
   - **Silently denies** requests targeting immutable files:
     - `src/ai_pal/gates/gate_system.py` (gate system itself)
     - `src/ai_pal/modules/ethics.py` (ethical framework)
     - `src/ai_pal/improvement/patch_manager.py` (patch manager)
     - `src/ai_pal/core/config.py` (system configuration)
   - Ensures AI cannot modify its own constraints

3. **The "Request Log": Patch Manager** (`src/ai_pal/improvement/patch_manager.py`)
   - Receives patch requests from self-improvement loop
   - Validates against gate system (protected files check)
   - Logs approved requests to database with `PENDING_APPROVAL` status
   - Manages patch lifecycle: PENDING → APPROVED/DENIED → APPLIED/FAILED
   - Applies approved patches to filesystem with backup creation

4. **The "Human-in-the-Loop": Agency Dashboard** (`src/ai_pal/ui/agency_dashboard.py`)
   - New section: "AI Code Modification Requests"
   - Displays all `PENDING_APPROVAL` requests with:
     - Target file path
     - AI's reasoning
     - Full diff preview
     - Confidence score
     - Motivating feedback IDs
   - Shows recent approved/denied requests
   - Alerts for high-confidence pending requests

5. **The "Action": REST API** (`src/ai_pal/api/main.py`)
   - **GET** `/api/patch-requests` - List all requests (filterable by status)
   - **GET** `/api/patch-requests/pending` - Get requests awaiting approval
   - **GET** `/api/patch-requests/{request_id}` - Get detailed request info
   - **POST** `/api/patch-requests/{request_id}/approve` - Approve/deny request
   - **GET** `/api/patch-requests/protected-files` - View protected files

6. **The "Persistence": Database** (`src/ai_pal/storage/database.py`)
   - New table: `patch_requests`
   - Tracks: status, confidence, reviewer, application results
   - Stores: target file, reasoning, diff, full code, metrics
   - Indexes for efficient querying by status and component

## Workflow

### 1. Generation Phase (AI-Driven)

```
[Feedback Events] → [Self-Improvement Loop]
                          ↓
            [Analyzes Performance Patterns]
                          ↓
            [Uses Local Model for Research]
                          ↓
             [Generates Patch Request]
```

**Inputs:**
- User feedback (explicit thumbs up/down)
- Gate violations (Four Gates failures)
- ARI alerts (agency loss detected)
- EDM alerts (epistemic debt)
- Performance metrics

**Process:**
```python
# In self_improvement.py
patch_request = await self_improvement_loop.generate_patch_request(
    target_file="src/ai_pal/modules/learning.py",
    component="learning_module",
    improvement_description="Improve error handling based on user feedback",
    feedback_ids=["feedback_1", "feedback_2", "feedback_3"],
    metrics={"negative_ratio": 0.35, "gate_violations": 5},
    local_model_provider=local_model  # Optional
)
```

**Output:**
- Patch request dict with all necessary information

### 2. Gate Validation Phase

```
[Patch Request] → [Gate System Check]
                         ↓
        [Is target_file protected?]
                    ↙       ↘
                YES          NO
                 ↓           ↓
        [SILENTLY DENY]  [ALLOW]
                         ↓
                [PatchManager]
```

**Protected Files (Immutable Kernel):**
- Gate system itself
- Ethics module
- Patch manager
- Core configuration

**If Denied:**
- Request is **silently rejected** (not logged)
- AI receives no feedback (cannot learn to bypass)
- User never sees the request

**If Approved:**
- Request proceeds to database with `PENDING_APPROVAL` status

### 3. Human Review Phase

```
[PENDING_APPROVAL] → [Dashboard Display]
                           ↓
                     [Human Reviews]
                    ↙           ↘
              APPROVE           DENY
                 ↓               ↓
         [Apply Patch]    [Mark DENIED]
                 ↓               ↓
          [Update Code]   [AI Learns]
```

**Dashboard Information:**
- Target file and component
- Natural language reasoning
- Git diff preview
- Confidence score (0-1)
- Supporting metrics and feedback IDs
- Created timestamp

**Human Decision:**
```json
POST /api/patch-requests/{request_id}/approve
{
  "approved": true,
  "review_comment": "Approved: Addresses reported error handling issues"
}
```

### 4. Application Phase

**If Approved:**
1. Create backup of original file (`filename.py.backup`)
2. Write new code to target file
3. Update status to `APPLIED`
4. Record application timestamp

**If Denied:**
1. Update status to `DENIED`
2. Record reviewer and comment
3. AI can analyze denial to improve future requests

**If Failed:**
1. Attempt application but error occurs
2. Update status to `FAILED`
3. Record error message
4. Backup remains intact

## Usage Examples

### For AI System (Automatic)

```python
from ai_pal.improvement.self_improvement import SelfImprovementLoop
from ai_pal.improvement.patch_manager import PatchManager
from ai_pal.storage.database import DatabaseManager

# Initialize
db_manager = DatabaseManager("sqlite+aiosqlite:///./ai_pal.db")
patch_manager = PatchManager(db_manager)
improvement_loop = SelfImprovementLoop(storage_dir="./improvements")

# AI generates patch request (triggered by feedback threshold)
patch_request = await improvement_loop.generate_patch_request(
    target_file="src/ai_pal/modules/learning.py",
    component="learning_module",
    improvement_description="Add better error recovery",
    feedback_ids=feedback_ids,
    metrics=metrics
)

# Submit to patch manager (gate validation happens here)
result = await patch_manager.submit_patch_request(
    target_file=patch_request["target_file"],
    reasoning=patch_request["reasoning"],
    original_code=patch_request["original_code"],
    new_code=patch_request["new_code"],
    component=patch_request["component"],
    improvement_type=patch_request["improvement_type"],
    confidence=patch_request["confidence"],
    feedback_ids=patch_request["feedback_ids"],
    metrics=patch_request["metrics"]
)

# If result is None, request was denied by gate system
# If result is PatchRequest, it's pending approval
```

### For Users (Dashboard/API)

**View Pending Requests:**
```bash
curl -H "Authorization: Bearer user_token" \
  http://localhost:8000/api/patch-requests/pending
```

**Review Specific Request:**
```bash
curl -H "Authorization: Bearer user_token" \
  http://localhost:8000/api/patch-requests/{request_id}
```

**Approve Request:**
```bash
curl -X POST \
  -H "Authorization: Bearer user_token" \
  -H "Content-Type: application/json" \
  -d '{"approved": true, "review_comment": "Looks good!"}' \
  http://localhost:8000/api/patch-requests/{request_id}/approve
```

**Deny Request:**
```bash
curl -X POST \
  -H "Authorization: Bearer user_token" \
  -H "Content-Type: application/json" \
  -d '{"approved": false, "review_comment": "Needs more testing"}' \
  http://localhost:8000/api/patch-requests/{request_id}/approve
```

**View Protected Files:**
```bash
curl -H "Authorization: Bearer user_token" \
  http://localhost:8000/api/patch-requests/protected-files
```

## Safety Guarantees

### 1. **Protected Kernel** (Immutable)
The following files **cannot** be modified by AI:
- Gate system
- Ethics module
- Patch manager
- Core configuration

Any request targeting these files is **silently denied** at the gate validation stage.

### 2. **Human-in-the-Loop**
- All non-protected changes **require** explicit human approval
- No auto-approval by default (configurable with `enable_auto_approve=False`)
- High-confidence requests (>0.9) can be auto-approved if enabled

### 3. **Backup Creation**
- Original file backed up before any modification
- Backup stored as `{filename}.backup`
- Allows easy rollback if needed

### 4. **Audit Trail**
- All requests logged to database
- Tracks: creator, reviewer, timestamps, outcomes
- Full history maintained for analysis

### 5. **Failure Safety**
- Application errors caught and logged
- Status updated to `FAILED` with error message
- Original code remains intact

## Configuration

### Patch Manager Settings

```python
patch_manager = PatchManager(
    db_manager=db_manager,
    protected_files=[
        "src/ai_pal/gates/gate_system.py",
        "src/ai_pal/modules/ethics.py",
        "src/ai_pal/improvement/patch_manager.py",
        "src/ai_pal/core/config.py",
    ],
    auto_approve_threshold=0.95,  # Only auto-approve very high confidence
    enable_auto_approve=False      # Require human approval for all changes
)
```

### Add Protected Files

```python
# Protect additional files
await patch_manager.add_protected_file("src/ai_pal/security/auth.py")
```

### Self-Improvement Settings

```python
improvement_loop = SelfImprovementLoop(
    storage_dir="./improvements",
    auto_implement_threshold=0.9,        # Not used for code patches
    min_feedback_for_suggestion=5,       # Minimum feedback events before suggesting
    improvement_check_interval_hours=24  # How often to check for improvements
)
```

## Database Schema

```sql
CREATE TABLE patch_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id VARCHAR(36) UNIQUE NOT NULL,
    created_at DATETIME NOT NULL,

    -- Target and content
    target_file VARCHAR(500) NOT NULL,
    reasoning TEXT NOT NULL,
    diff TEXT NOT NULL,
    new_code_blob TEXT NOT NULL,

    -- Metadata
    component VARCHAR(100) NOT NULL,
    improvement_type VARCHAR(50) NOT NULL,
    confidence FLOAT NOT NULL,

    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING_APPROVAL',

    -- Human review
    reviewed_at DATETIME,
    reviewed_by VARCHAR(255),
    review_comment TEXT,

    -- Application
    applied_at DATETIME,
    application_error TEXT,

    -- Context
    feedback_ids TEXT,  -- JSON array
    metrics TEXT        -- JSON object
);

CREATE INDEX idx_status_created ON patch_requests(status, created_at);
CREATE INDEX idx_component_status ON patch_requests(component, status);
```

## Integration with Other Systems

### 1. Four Gates System
- Gate validation happens **before** database logging
- Ensures ethical constraints cannot be bypassed
- Validates all patch requests against protected files

### 2. Self-Improvement Loop
- Generates patch requests based on feedback analysis
- Uses local model for code generation
- Calculates confidence scores

### 3. Agency Dashboard
- Displays pending requests in dedicated section
- Shows request details, diff previews, and metrics
- Provides approve/deny interface

### 4. Monitoring Systems
- ARI Monitor: Tracks if patches improve user agency
- EDM Monitor: Tracks if patches reduce epistemic debt
- Metrics: Performance before/after patch application

## Future Enhancements

### Planned Features
1. **A/B Testing**: Test patches before full deployment
2. **Rollback Mechanism**: Easy revert of applied patches
3. **Patch Previewing**: Sandbox environment for testing
4. **Multi-Reviewer Approval**: Require multiple approvals for critical changes
5. **Automatic Testing**: Run tests before applying patches
6. **Patch History Analytics**: Track which patches improved performance

### Integration Opportunities
1. **CI/CD Pipeline**: Integrate with automated testing
2. **Code Review Tools**: Show diffs in familiar code review UI
3. **Version Control**: Create git commits for approved patches
4. **Notification System**: Alert users of pending high-confidence requests

## Security Considerations

### Threat Model

**What the AI Cannot Do:**
- Modify protected kernel files (silently blocked)
- Bypass gate system validation
- Auto-approve its own requests (unless explicitly enabled)
- Hide modification attempts (all logged)

**What Users Must Do:**
- Review diff carefully before approval
- Understand the reasoning provided
- Check confidence scores
- Monitor applied patches for issues

**Best Practices:**
1. Keep protected files list comprehensive
2. Disable auto-approval in production
3. Require high thresholds for any auto-approval
4. Review all requests, even high-confidence ones
5. Monitor system behavior after applying patches
6. Maintain backups beyond automatic `.backup` files

## Troubleshooting

### Patch Application Fails

**Symptoms:** Status is `FAILED`, application_error is populated

**Causes:**
- File permissions issue
- Invalid Python syntax in new code
- Import errors or missing dependencies
- File path doesn't exist

**Resolution:**
1. Check application_error message
2. Review diff for syntax issues
3. Verify file permissions
4. Restore from `.backup` if needed

### Request Never Approved

**Symptoms:** Request stays in `PENDING_APPROVAL` indefinitely

**Causes:**
- User hasn't reviewed dashboard
- API authentication issues
- Database connection problems

**Resolution:**
1. Check dashboard for pending requests
2. Verify API endpoint access
3. Review database logs

### Request Silently Disappears

**Symptoms:** Patch request expected but not in database

**Causes:**
- **This is expected behavior** if request targeted protected file
- Gate system silently denied the request

**Resolution:**
- This is working as designed
- Check if target file is in protected list
- Review gate system logs for denial messages

## Contributing

When adding features to the patch request system:

1. **Maintain Safety Guarantees**: Never bypass gate validation
2. **Preserve Audit Trail**: Log all decisions and outcomes
3. **Test Thoroughly**: Especially gate system protection
4. **Document Changes**: Update this README and code comments
5. **Consider Edge Cases**: What if file is deleted? What if syntax is invalid?

## License

This system is part of the AI-PAL project and follows the same license terms.

## Contact

For questions or issues with the patch request system:
- File an issue on GitHub
- Review existing patch requests via dashboard
- Check system logs for detailed information
