"""Custom exceptions for company_ai SDK."""


class CompanyAIError(Exception):
    """Base exception for company_ai."""


class ConfigurationError(CompanyAIError):
    """Raised when required configuration is missing."""


class LangfuseConnectionError(CompanyAIError):
    """Raised when Langfuse is unreachable."""
