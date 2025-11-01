"""
Security Module - Comprehensive Security Infrastructure

Provides complete security capabilities including:
- Credential management
- Secret scanning
- Input sanitization and output validation
- Comprehensive audit logging

Part of Phase 1 Full Implementation.
"""

from ..core.credentials import SecureCredentialManager as CredentialManager

# Secret scanning
from .secret_scanner import (
    SecretScanner,
    SecretType,
    SecretSeverity,
    SecretMatch,
    get_scanner,
    scan_text,
    scan_file,
)

# Input/output security
from .sanitization import (
    InputSanitizer,
    OutputValidator,
    SecurityValidator,
    SanitizationLevel,
    SanitizationResult,
    get_validator,
    sanitize_input,
    validate_output,
)

# Audit logging
from .audit_log import (
    AuditLogger,
    AuditEvent,
    AuditEventType,
    AuditSeverity,
    get_audit_logger,
    log_audit_event,
    audit_gate_evaluation,
    audit_plugin_loaded,
    audit_secret_detected,
    audit_model_request,
)

__all__ = [
    # Credential management
    'CredentialManager',

    # Secret scanning
    'SecretScanner',
    'SecretType',
    'SecretSeverity',
    'SecretMatch',
    'get_scanner',
    'scan_text',
    'scan_file',

    # Sanitization
    'InputSanitizer',
    'OutputValidator',
    'SecurityValidator',
    'SanitizationLevel',
    'SanitizationResult',
    'get_validator',
    'sanitize_input',
    'validate_output',

    # Audit logging
    'AuditLogger',
    'AuditEvent',
    'AuditEventType',
    'AuditSeverity',
    'get_audit_logger',
    'log_audit_event',
    'audit_gate_evaluation',
    'audit_plugin_loaded',
    'audit_secret_detected',
    'audit_model_request',
]
