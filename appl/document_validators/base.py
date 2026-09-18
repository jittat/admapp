from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    """Outcome of a custom document validator.

    code identifies the rejection reason ('' when valid). On rejection the
    message is rendered from
    appl/include/document_validation_errors/<validator key>.html (falling back
    to default.html), which receives code, context and
    project_uploaded_document and branches on code. context carries optional
    extra details for the message; no validator uses it yet.

    Besides the validator's own codes, run_document_validator also rejects
    with 'misconfigured' and 'verification_error'; those messages are in
    default.html, so <key>.html should include it for codes it does not handle.
    """
    is_valid: bool
    code: str = ''
    context: dict = field(default_factory=dict)

    @classmethod
    def accept(cls):
        return cls(True)

    @classmethod
    def reject(cls, code, **context):
        return cls(False, code, context)
