"""
Credential Manager - Bridge to Phase 1 Implementation

Bridges Phase 2-3 expectations to actual Phase 1 implementation.
The actual implementation is in core.credentials.SecureCredentialManager.
"""

from ..core.credentials import SecureCredentialManager as CredentialManager

__all__ = ['CredentialManager']
