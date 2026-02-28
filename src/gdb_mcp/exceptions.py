"""Exception types for gdb-mcp."""


class GdbSessionError(RuntimeError):
    """Base exception for session-level errors."""


class SessionNotFoundError(GdbSessionError):
    """Raised when a session id does not exist."""


class GdbCommandTimeoutError(GdbSessionError):
    """Raised when a command exceeds the configured timeout."""
