"""Offline model-route qualification and request validation helpers.

These helpers validate declared data. They are not a trusted dispatcher,
Supervisor, permission system, or OS isolation boundary.
"""

from .routing import (
    authorize_request,
    execution_record,
    native_child_request,
    validate_dispatch_observation,
)

__all__ = [
    "authorize_request",
    "execution_record",
    "native_child_request",
    "validate_dispatch_observation",
]
