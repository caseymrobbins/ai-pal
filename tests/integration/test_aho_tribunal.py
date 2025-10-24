"""
Integration tests for AHO Tribunal interface.

Tests Override-Restore-Repair workflow and appeals processing.
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from ai_pal.api.aho_tribunal import (
    app,
    db,
    Appeal,
    AppealStatus,
    AppealPriority,
    submit_appeal,
    OverrideAction,
    RestoreAction,
)


@pytest.fixture
def client():
    """Create FastAPI test client."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_db():
    """Clear database before each test."""
    db.appeals = {}
    db.repair_tickets = {}
    db.audit_log = []
    yield


# ============================================================================
# Appeal Submission Tests
# ============================================================================

@pytest.mark.integration
def test_submit_appeal():
    """Test submitting a new appeal."""
    appeal_id = submit_appeal(
        user_id="user_123",
        action_id="ACTION-001",
        ai_decision="Content flagged as spam",
        user_complaint="This is not spam",
        decision_context={"confidence": 0.85},
        priority=AppealPriority.HIGH,
    )

    assert appeal_id is not None
    assert appeal_id.startswith("APPEAL-")
    assert appeal_id in db.appeals


@pytest.mark.integration
def test_appeal_stored_correctly():
    """Test appeal is stored with correct data."""
    appeal_id = submit_appeal(
        user_id="user_456",
        action_id="ACTION-002",
        ai_decision="Account suspended",
        user_complaint="Suspension was unfair",
        decision_context={"reason": "spam_detection"},
    )

    appeal = db.get_appeal(appeal_id)
    assert appeal is not None
    assert appeal.user_id == "user_456"
    assert appeal.status == AppealStatus.PENDING
    assert appeal.override_executed is False


# ============================================================================
# API Endpoint Tests
# ============================================================================

@pytest.mark.integration
def test_get_dashboard(client):
    """Test dashboard endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


@pytest.mark.integration
def test_list_appeals_empty(client):
    """Test listing appeals when none exist."""
    response = client.get("/api/appeals")
    assert response.status_code == 200

    data = response.json()
    assert "appeals" in data
    assert len(data["appeals"]) == 0


@pytest.mark.integration
def test_list_appeals_with_data(client, sample_appeal):
    """Test listing appeals with data."""
    db.add_appeal(sample_appeal)

    response = client.get("/api/appeals")
    assert response.status_code == 200

    data = response.json()
    assert len(data["appeals"]) == 1
    assert data["appeals"][0]["appeal_id"] == sample_appeal.appeal_id


@pytest.mark.integration
def test_get_appeal_by_id(client, sample_appeal):
    """Test getting specific appeal by ID."""
    db.add_appeal(sample_appeal)

    response = client.get(f"/api/appeals/{sample_appeal.appeal_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["appeal_id"] == sample_appeal.appeal_id
    assert data["user_id"] == sample_appeal.user_id


@pytest.mark.integration
def test_get_nonexistent_appeal(client):
    """Test getting appeal that doesn't exist."""
    response = client.get("/api/appeals/NONEXISTENT")
    assert response.status_code == 404


# ============================================================================
# Override-Restore-Repair Workflow Tests
# ============================================================================

@pytest.mark.integration
def test_override_step(client, sample_appeal):
    """Test Override step of Override-Restore-Repair loop."""
    db.add_appeal(sample_appeal)

    override_data = {
        "appeal_id": sample_appeal.appeal_id,
        "reviewer_id": "reviewer_001",
        "decision": "approve",
        "notes": "AI made an error - reinstating user",
    }

    response = client.post(
        f"/api/appeals/{sample_appeal.appeal_id}/override",
        json=override_data,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["next_step"] == "restore"

    # Check appeal updated
    appeal = db.get_appeal(sample_appeal.appeal_id)
    assert appeal.status == AppealStatus.APPROVED
    assert appeal.override_executed is True
    assert appeal.reviewer_id == "reviewer_001"


@pytest.mark.integration
def test_restore_step(client, sample_appeal):
    """Test Restore step of Override-Restore-Repair loop."""
    # First do override
    sample_appeal.override_executed = True
    db.add_appeal(sample_appeal)

    restore_data = {
        "appeal_id": sample_appeal.appeal_id,
        "reviewer_id": "reviewer_001",
        "restoration_type": "reinstate_access",
    }

    response = client.post(
        f"/api/appeals/{sample_appeal.appeal_id}/restore",
        json=restore_data,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["next_step"] == "repair"

    # Check appeal updated
    appeal = db.get_appeal(sample_appeal.appeal_id)
    assert appeal.restore_executed is True


@pytest.mark.integration
def test_restore_before_override_fails(client, sample_appeal):
    """Test that restore fails if override hasn't been executed."""
    db.add_appeal(sample_appeal)  # No override executed

    restore_data = {
        "appeal_id": sample_appeal.appeal_id,
        "reviewer_id": "reviewer_001",
        "restoration_type": "reinstate_access",
    }

    response = client.post(
        f"/api/appeals/{sample_appeal.appeal_id}/restore",
        json=restore_data,
    )

    assert response.status_code == 400
    assert "Must execute override first" in response.json()["detail"]


@pytest.mark.integration
def test_repair_step_creates_ticket(client, sample_appeal):
    """Test Repair step creates engineering ticket."""
    # Set up appeal with override and restore complete
    sample_appeal.override_executed = True
    sample_appeal.restore_executed = True
    db.add_appeal(sample_appeal)

    response = client.post(
        f"/api/appeals/{sample_appeal.appeal_id}/repair",
        params={"reviewer_id": "reviewer_001"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "ticket_id" in data
    assert data["appeal_completed"] is True

    # Check appeal completed
    appeal = db.get_appeal(sample_appeal.appeal_id)
    assert appeal.repair_ticket_created is True
    assert appeal.status == AppealStatus.COMPLETED

    # Check ticket created
    ticket_id = data["ticket_id"]
    assert ticket_id in db.repair_tickets


@pytest.mark.integration
def test_repair_before_restore_fails(client, sample_appeal):
    """Test that repair fails if restore hasn't been executed."""
    sample_appeal.override_executed = True  # But not restore
    db.add_appeal(sample_appeal)

    response = client.post(
        f"/api/appeals/{sample_appeal.appeal_id}/repair",
        params={"reviewer_id": "reviewer_001"},
    )

    assert response.status_code == 400
    assert "Must execute restore first" in response.json()["detail"]


# ============================================================================
# Complete Override-Restore-Repair Workflow
# ============================================================================

@pytest.mark.integration
def test_complete_orr_workflow(client, sample_appeal):
    """Test complete Override-Restore-Repair workflow."""
    db.add_appeal(sample_appeal)

    # Step 1: Override
    override_response = client.post(
        f"/api/appeals/{sample_appeal.appeal_id}/override",
        json={
            "appeal_id": sample_appeal.appeal_id,
            "reviewer_id": "reviewer_001",
            "decision": "approve",
            "notes": "Approved",
        },
    )
    assert override_response.status_code == 200

    # Step 2: Restore
    restore_response = client.post(
        f"/api/appeals/{sample_appeal.appeal_id}/restore",
        json={
            "appeal_id": sample_appeal.appeal_id,
            "reviewer_id": "reviewer_001",
            "restoration_type": "reinstate_access",
        },
    )
    assert restore_response.status_code == 200

    # Step 3: Repair
    repair_response = client.post(
        f"/api/appeals/{sample_appeal.appeal_id}/repair",
        params={"reviewer_id": "reviewer_001"},
    )
    assert repair_response.status_code == 200

    # Verify final state
    appeal = db.get_appeal(sample_appeal.appeal_id)
    assert appeal.status == AppealStatus.COMPLETED
    assert appeal.override_executed is True
    assert appeal.restore_executed is True
    assert appeal.repair_ticket_created is True


# ============================================================================
# Audit Trail Tests
# ============================================================================

@pytest.mark.integration
def test_audit_log_records_actions(client, sample_appeal):
    """Test that all actions are logged to audit trail."""
    db.add_appeal(sample_appeal)

    # Clear audit log
    db.audit_log = []

    # Perform override
    client.post(
        f"/api/appeals/{sample_appeal.appeal_id}/override",
        json={
            "appeal_id": sample_appeal.appeal_id,
            "reviewer_id": "reviewer_001",
            "decision": "approve",
            "notes": "Test",
        },
    )

    # Check audit log
    response = client.get("/api/audit-log")
    assert response.status_code == 200

    data = response.json()
    assert len(data["audit_log"]) > 0

    # Find override action
    override_logs = [
        log for log in data["audit_log"] if log["action"] == "override_executed"
    ]
    assert len(override_logs) == 1
    assert override_logs[0]["appeal_id"] == sample_appeal.appeal_id


@pytest.mark.integration
def test_audit_log_limit(client):
    """Test audit log respects limit parameter."""
    # Add many log entries
    for i in range(150):
        db.audit_log.append({
            "timestamp": datetime.now().isoformat(),
            "action": f"test_action_{i}",
            "appeal_id": f"APPEAL-{i}",
        })

    response = client.get("/api/audit-log?limit=50")
    data = response.json()

    assert len(data["audit_log"]) == 50


# ============================================================================
# Repair Ticket Tests
# ============================================================================

@pytest.mark.integration
def test_list_repair_tickets_empty(client):
    """Test listing repair tickets when none exist."""
    response = client.get("/api/repair-tickets")
    assert response.status_code == 200

    data = response.json()
    assert "tickets" in data
    assert len(data["tickets"]) == 0


@pytest.mark.integration
def test_repair_ticket_contains_context(client, sample_appeal):
    """Test repair ticket includes full appeal context."""
    sample_appeal.override_executed = True
    sample_appeal.restore_executed = True
    db.add_appeal(sample_appeal)

    # Create repair ticket
    response = client.post(
        f"/api/appeals/{sample_appeal.appeal_id}/repair",
        params={"reviewer_id": "reviewer_001"},
    )

    ticket_id = response.json()["ticket_id"]
    ticket = db.repair_tickets[ticket_id]

    # Ticket should include appeal context
    assert sample_appeal.ai_decision in ticket.description
    assert sample_appeal.user_complaint in ticket.description
    assert ticket.priority == sample_appeal.priority.value


# ============================================================================
# Health Check Tests
# ============================================================================

@pytest.mark.integration
def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "aho_tribunal"
    assert "pending_appeals" in data


# ============================================================================
# Filtering Tests
# ============================================================================

@pytest.mark.integration
def test_filter_appeals_by_status(client):
    """Test filtering appeals by status."""
    # Create appeals with different statuses
    appeal1 = Appeal(
        appeal_id="APPEAL-1",
        user_id="user1",
        action_id="ACTION-1",
        timestamp=datetime.now(),
        status=AppealStatus.PENDING,
        priority=AppealPriority.HIGH,
        ai_decision="Test",
        user_complaint="Test",
        decision_context={},
    )

    appeal2 = Appeal(
        appeal_id="APPEAL-2",
        user_id="user2",
        action_id="ACTION-2",
        timestamp=datetime.now(),
        status=AppealStatus.UNDER_REVIEW,
        priority=AppealPriority.HIGH,
        ai_decision="Test",
        user_complaint="Test",
        decision_context={},
    )

    db.add_appeal(appeal1)
    db.add_appeal(appeal2)

    # Filter by PENDING
    response = client.get("/api/appeals?status=pending")
    data = response.json()

    assert len(data["appeals"]) == 1
    assert data["appeals"][0]["status"] == "pending"


@pytest.mark.integration
def test_filter_appeals_by_priority(client):
    """Test filtering appeals by priority."""
    appeal1 = Appeal(
        appeal_id="APPEAL-1",
        user_id="user1",
        action_id="ACTION-1",
        timestamp=datetime.now(),
        status=AppealStatus.PENDING,
        priority=AppealPriority.HIGH,
        ai_decision="Test",
        user_complaint="Test",
        decision_context={},
    )

    appeal2 = Appeal(
        appeal_id="APPEAL-2",
        user_id="user2",
        action_id="ACTION-2",
        timestamp=datetime.now(),
        status=AppealStatus.PENDING,
        priority=AppealPriority.LOW,
        ai_decision="Test",
        user_complaint="Test",
        decision_context={},
    )

    db.add_appeal(appeal1)
    db.add_appeal(appeal2)

    # Filter by HIGH priority
    response = client.get("/api/appeals?priority=high")
    data = response.json()

    assert len(data["appeals"]) == 1
    assert data["appeals"][0]["priority"] == "high"
