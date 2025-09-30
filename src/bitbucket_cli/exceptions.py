"""
ABOUTME: Custom exception classes for Bitbucket CLI with specific error types and messages
ABOUTME: Provides structured error handling for API errors, authentication, and configuration issues
"""


class BitbucketCLIError(Exception):
    """Base exception for all Bitbucket CLI errors."""
    pass


class BitbucketAPIError(BitbucketCLIError):
    """General API error from Bitbucket Cloud."""
    pass


class AuthenticationError(BitbucketCLIError):
    """Authentication failed or credentials invalid."""
    pass


class PermissionError(BitbucketCLIError):
    """Insufficient permissions for the requested operation."""
    pass


class NotFoundError(BitbucketCLIError):
    """Requested resource (repository, PR, user) not found."""
    pass


class ConflictError(BitbucketCLIError):
    """Operation conflicts with current state (e.g., PR already merged)."""
    pass


class RateLimitError(BitbucketCLIError):
    """API rate limit exceeded."""
    pass


class ConfigurationError(BitbucketCLIError):
    """Configuration file error or invalid settings."""
    pass


class GitError(BitbucketCLIError):
    """Git repository or operation error."""
    pass


class ValidationError(BitbucketCLIError):
    """Input validation error."""
    pass