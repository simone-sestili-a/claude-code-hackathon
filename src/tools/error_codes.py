from pydantic import BaseModel


class ToolResult(BaseModel):
    success: bool
    data: dict | None = None
    is_error: bool = False
    error_code: str | None = None
    error_reason: str | None = None
    retry_guidance: str | None = None


ERROR_CODES = {
    "NOT_FOUND": "The requested resource was not found.",
    "FROZEN_ACCOUNT": "Account is frozen; no actions permitted until unfrozen by authorized personnel.",
    "PII_DETECTED": "PII pattern detected in parameters; request blocked by security policy.",
    "EXTERNAL_EMAIL": "External email domain is not permitted for automated sends.",
    "SECURITY_CLOSE_BLOCKED": "Security incidents cannot be auto-closed; requires human review.",
    "LOOP_GUARD": "Maximum retry count reached; escalating to human.",
    "PERMISSION_DENIED": "Caller does not have permission for this action.",
    "VALIDATION_ERROR": "Input did not match expected schema.",
}
