from typing import Optional, Any, Dict

class SmartDocException(Exception):
    """Base exception for all domain-specific SmartDoc errors."""
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: str = "SMARTDOC_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}


class UnsupportedFileTypeError(SmartDocException):
    """Raised when an uploaded document file extension or MIME type is not supported."""
    def __init__(self, message: str = "Unsupported file type.", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code="UNSUPPORTED_FILE_TYPE",
            details=details
        )


class ExtractionFailedError(SmartDocException):
    """Raised when text or table content extraction from a document fails."""
    def __init__(self, message: str = "Document extraction failed.", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="EXTRACTION_FAILED",
            details=details
        )


class LLMProviderUnavailableError(SmartDocException):
    """Raised when local Ollama or remote LLM service is unreachable or fails."""
    def __init__(self, message: str = "LLM provider is currently unavailable.", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=503,
            error_code="LLM_PROVIDER_UNAVAILABLE",
            details=details
        )


class ValidationFailedError(SmartDocException):
    """Raised when numeric fact checking or citation verification fails."""
    def __init__(self, message: str = "Fact verification or citation check failed.", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code="VALIDATION_FAILED",
            details=details
        )


class DocumentNotFoundError(SmartDocException):
    """Raised when a requested document ID does not exist in the store."""
    def __init__(self, message: str = "Document not found.", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=404,
            error_code="DOCUMENT_NOT_FOUND",
            details=details
        )
