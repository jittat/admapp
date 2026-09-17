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
    if document_url is not None:
        if document_url.startswith('https://student.mytcas.com/view-folio/'):
            return ValidationResult.accept()
        return ValidationResult.reject('invalid_url')
    return ValidationResult.reject('no_document')
