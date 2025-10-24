"""
Appeals & Humanity Override (AHO) Tribunal Interface.

Web dashboard for human reviewers to:
1. View appeals from users
2. Override AI decisions
3. Restore affected users
4. Generate repair tickets for engineering

This implements Gate 3 of the AC-AI framework.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from loguru import logger


# === Data Models ===

class AppealStatus(Enum):
    """Status of an appeal."""

    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    DENIED = "denied"
    COMPLETED = "completed"


class AppealPriority(Enum):
    """Priority level of appeal."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Appeal:
    """User appeal against an AI decision."""

    appeal_id: str
    user_id: str
    action_id: str  # ID of the contested AI action
    timestamp: datetime
    status: AppealStatus
    priority: AppealPriority

    # Appeal details
    ai_decision: str  # What the AI decided
    user_complaint: str  # Why user is appealing
    decision_context: Dict[str, Any]  # Full context of AI decision

    # Review details
    reviewer_id: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None

    # Override-Restore-Repair
    override_executed: bool = False
    restore_executed: bool = False
    repair_ticket_created: bool = False
    repair_ticket_id: Optional[str] = None


class OverrideAction(BaseModel):
    """Request to override an AI decision."""

    appeal_id: str
    reviewer_id: str
    decision: str  # "approve" or "deny"
    notes: str


class RestoreAction(BaseModel):
    """Request to restore a user."""

    appeal_id: str
    reviewer_id: str
    restoration_type: str  # e.g., "refund", "reinstate_access", "publish_correction"


class RepairTicket(BaseModel):
    """Engineering repair ticket."""

    ticket_id: str
    appeal_id: str
    created_at: datetime
    priority: str
    title: str
    description: str
    root_cause: str
    proposed_fix: str
    assigned_to: Optional[str] = None
    status: str = "open"


# === In-Memory Storage (Production would use database) ===

class AHODatabase:
    """In-memory database for AHO system."""

    def __init__(self):
        self.appeals: Dict[str, Appeal] = {}
        self.repair_tickets: Dict[str, RepairTicket] = {}
        self.audit_log: List[Dict[str, Any]] = []

        # Load from disk if exists
        self._load_from_disk()

    def _load_from_disk(self) -> None:
        """Load appeals from disk."""
        data_file = Path("data/aho_appeals.json")
        if data_file.exists():
            try:
                with open(data_file, "r") as f:
                    data = json.load(f)
                    # Would deserialize appeals here
                logger.info(f"Loaded {len(self.appeals)} appeals from disk")
            except Exception as e:
                logger.error(f"Failed to load appeals: {e}")

    def _save_to_disk(self) -> None:
        """Save appeals to disk."""
        data_file = Path("data/aho_appeals.json")
        data_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Would serialize appeals here
            logger.debug("Saved appeals to disk")
        except Exception as e:
            logger.error(f"Failed to save appeals: {e}")

    def add_appeal(self, appeal: Appeal) -> None:
        """Add an appeal."""
        self.appeals[appeal.appeal_id] = appeal
        self._save_to_disk()

        self.audit_log.append({
            "timestamp": datetime.now().isoformat(),
            "action": "appeal_created",
            "appeal_id": appeal.appeal_id,
            "user_id": appeal.user_id,
        })

    def get_appeal(self, appeal_id: str) -> Optional[Appeal]:
        """Get an appeal by ID."""
        return self.appeals.get(appeal_id)

    def list_appeals(
        self,
        status: Optional[AppealStatus] = None,
        priority: Optional[AppealPriority] = None,
    ) -> List[Appeal]:
        """List appeals with optional filtering."""
        appeals = list(self.appeals.values())

        if status:
            appeals = [a for a in appeals if a.status == status]

        if priority:
            appeals = [a for a in appeals if a.priority == priority]

        # Sort by timestamp (newest first)
        appeals.sort(key=lambda a: a.timestamp, reverse=True)

        return appeals

    def update_appeal(self, appeal: Appeal) -> None:
        """Update an appeal."""
        self.appeals[appeal.appeal_id] = appeal
        self._save_to_disk()


# === FastAPI Application ===

app = FastAPI(
    title="AHO Tribunal",
    description="Appeals & Humanity Override Dashboard",
    version="0.1.0",
)

# Database
db = AHODatabase()

# Templates
templates = Jinja2Templates(directory="src/ai_pal/api/templates")


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard."""
    pending_appeals = db.list_appeals(status=AppealStatus.PENDING)
    under_review = db.list_appeals(status=AppealStatus.UNDER_REVIEW)

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "pending_count": len(pending_appeals),
            "under_review_count": len(under_review),
            "total_appeals": len(db.appeals),
        },
    )


@app.get("/api/appeals")
async def list_appeals(
    status: Optional[str] = None,
    priority: Optional[str] = None,
):
    """List all appeals."""
    status_enum = AppealStatus(status) if status else None
    priority_enum = AppealPriority(priority) if priority else None

    appeals = db.list_appeals(status=status_enum, priority=priority_enum)

    return {
        "appeals": [
            {
                **asdict(appeal),
                "timestamp": appeal.timestamp.isoformat(),
                "reviewed_at": appeal.reviewed_at.isoformat()
                if appeal.reviewed_at
                else None,
                "status": appeal.status.value,
                "priority": appeal.priority.value,
            }
            for appeal in appeals
        ]
    }


@app.get("/api/appeals/{appeal_id}")
async def get_appeal(appeal_id: str):
    """Get detailed appeal information."""
    appeal = db.get_appeal(appeal_id)

    if not appeal:
        raise HTTPException(status_code=404, detail="Appeal not found")

    return {
        **asdict(appeal),
        "timestamp": appeal.timestamp.isoformat(),
        "reviewed_at": appeal.reviewed_at.isoformat() if appeal.reviewed_at else None,
        "status": appeal.status.value,
        "priority": appeal.priority.value,
    }


@app.post("/api/appeals/{appeal_id}/override")
async def override_decision(appeal_id: str, action: OverrideAction):
    """
    Execute Override step of Override-Restore-Repair loop.

    This immediately reverses the AI's decision for the affected user.
    """
    appeal = db.get_appeal(appeal_id)

    if not appeal:
        raise HTTPException(status_code=404, detail="Appeal not found")

    logger.info(
        f"🔄 HUMANITY OVERRIDE: Appeal {appeal_id} by reviewer {action.reviewer_id}"
    )

    # Update appeal
    appeal.status = (
        AppealStatus.APPROVED if action.decision == "approve" else AppealStatus.DENIED
    )
    appeal.reviewer_id = action.reviewer_id
    appeal.reviewed_at = datetime.now()
    appeal.review_notes = action.notes
    appeal.override_executed = True

    db.update_appeal(appeal)

    # Log to audit trail
    db.audit_log.append({
        "timestamp": datetime.now().isoformat(),
        "action": "override_executed",
        "appeal_id": appeal_id,
        "reviewer_id": action.reviewer_id,
        "decision": action.decision,
    })

    logger.info(f"✓ Override executed: {action.decision}")

    return {
        "status": "success",
        "message": f"Override executed: {action.decision}",
        "next_step": "restore",
    }


@app.post("/api/appeals/{appeal_id}/restore")
async def restore_user(appeal_id: str, action: RestoreAction):
    """
    Execute Restore step of Override-Restore-Repair loop.

    This restores the user to their pre-action state (e.g., refund, reinstate access).
    """
    appeal = db.get_appeal(appeal_id)

    if not appeal:
        raise HTTPException(status_code=404, detail="Appeal not found")

    if not appeal.override_executed:
        raise HTTPException(
            status_code=400, detail="Must execute override first"
        )

    logger.info(
        f"🔧 RESTORE USER: Appeal {appeal_id} - Type: {action.restoration_type}"
    )

    # Execute restoration (in production, this would trigger actual restoration logic)
    appeal.restore_executed = True
    db.update_appeal(appeal)

    # Log to audit trail
    db.audit_log.append({
        "timestamp": datetime.now().isoformat(),
        "action": "restore_executed",
        "appeal_id": appeal_id,
        "reviewer_id": action.reviewer_id,
        "restoration_type": action.restoration_type,
    })

    logger.info(f"✓ Restoration executed: {action.restoration_type}")

    return {
        "status": "success",
        "message": f"User restored via: {action.restoration_type}",
        "next_step": "repair",
    }


@app.post("/api/appeals/{appeal_id}/repair")
async def create_repair_ticket(appeal_id: str, reviewer_id: str):
    """
    Execute Repair step of Override-Restore-Repair loop.

    Creates an engineering ticket to fix the underlying issue that caused the harm.
    """
    appeal = db.get_appeal(appeal_id)

    if not appeal:
        raise HTTPException(status_code=404, detail="Appeal not found")

    if not appeal.restore_executed:
        raise HTTPException(
            status_code=400, detail="Must execute restore first"
        )

    logger.info(f"🔨 CREATE REPAIR TICKET: Appeal {appeal_id}")

    # Generate repair ticket
    ticket_id = f"REPAIR-{appeal_id[-8:]}"

    ticket = RepairTicket(
        ticket_id=ticket_id,
        appeal_id=appeal_id,
        created_at=datetime.now(),
        priority=appeal.priority.value,
        title=f"Fix issue that caused Appeal {appeal_id}",
        description=(
            f"Root cause: {appeal.ai_decision}\n"
            f"User complaint: {appeal.user_complaint}\n"
            f"Context: {json.dumps(appeal.decision_context, indent=2)}"
        ),
        root_cause="To be analyzed by engineering team",
        proposed_fix="To be determined after root cause analysis",
    )

    db.repair_tickets[ticket_id] = ticket

    # Update appeal
    appeal.repair_ticket_created = True
    appeal.repair_ticket_id = ticket_id
    appeal.status = AppealStatus.COMPLETED
    db.update_appeal(appeal)

    # Log to audit trail
    db.audit_log.append({
        "timestamp": datetime.now().isoformat(),
        "action": "repair_ticket_created",
        "appeal_id": appeal_id,
        "ticket_id": ticket_id,
        "reviewer_id": reviewer_id,
    })

    logger.info(f"✓ Repair ticket created: {ticket_id}")

    return {
        "status": "success",
        "message": "Repair ticket created",
        "ticket_id": ticket_id,
        "appeal_completed": True,
    }


@app.get("/api/repair-tickets")
async def list_repair_tickets(status: Optional[str] = None):
    """List all repair tickets."""
    tickets = list(db.repair_tickets.values())

    if status:
        tickets = [t for t in tickets if t.status == status]

    return {
        "tickets": [
            {
                **ticket.dict(),
                "created_at": ticket.created_at.isoformat(),
            }
            for ticket in tickets
        ]
    }


@app.get("/api/audit-log")
async def get_audit_log(limit: int = 100):
    """Get audit trail of all AHO actions."""
    return {
        "audit_log": db.audit_log[-limit:],
        "total_entries": len(db.audit_log),
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "aho_tribunal",
        "version": "0.1.0",
        "pending_appeals": len(db.list_appeals(status=AppealStatus.PENDING)),
    }


# === Helper Functions for Integration ===

def submit_appeal(
    user_id: str,
    action_id: str,
    ai_decision: str,
    user_complaint: str,
    decision_context: Dict[str, Any],
    priority: AppealPriority = AppealPriority.MEDIUM,
) -> str:
    """
    Submit a new appeal (called from main system).

    Args:
        user_id: User submitting appeal
        action_id: ID of contested action
        ai_decision: What the AI decided
        user_complaint: User's reason for appeal
        decision_context: Full decision context
        priority: Priority level

    Returns:
        Appeal ID
    """
    appeal_id = f"APPEAL-{datetime.now().strftime('%Y%m%d%H%M%S')}-{user_id[-4:]}"

    appeal = Appeal(
        appeal_id=appeal_id,
        user_id=user_id,
        action_id=action_id,
        timestamp=datetime.now(),
        status=AppealStatus.PENDING,
        priority=priority,
        ai_decision=ai_decision,
        user_complaint=user_complaint,
        decision_context=decision_context,
    )

    db.add_appeal(appeal)

    logger.info(f"📝 New appeal submitted: {appeal_id}")

    return appeal_id


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting AHO Tribunal Interface...")
    logger.info("Access at: http://localhost:8001")

    uvicorn.run(app, host="0.0.0.0", port=8001)
