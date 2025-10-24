"""
Security Module - Bridge to Phase 1 Implementation

This module provides the interface expected by Phase 2-3 components while
bridging to the actual Phase 1 implementation in core.credentials.

Part of Phase 1.5 integration work.
"""

from ..core.credentials import SecureCredentialManager as CredentialManager

__all__ = ['CredentialManager']
