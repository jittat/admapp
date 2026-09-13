"""TCASFolio portfolios: a signed PDF from TCASFolio, or a TCASFolio link."""
from appl.document_validators.base import ValidationResult
from appl.pdfsignatures.verify import verify_with_profile


def validate(project_uploaded_document, uploaded_file=None, document_url=None):
    if uploaded_file is not None:
        check = verify_with_profile(uploaded_file.read(), 'tcasfolio')
        if check.ok:
            return ValidationResult.accept()
        return ValidationResult.reject(check.code)

    return validate_url(document_url)


def validate_url(document_url):
    # TODO: check against the TCASFolio url pattern once it is known.
    return ValidationResult.accept()
