from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    """Outcome of a custom document validator.

    code identifies the rejection reason; it selects the message in
    appl/include/document_validation_errors/<validator key>.html, which also
    receives context.
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
