"""Custom validators for ProjectUploadedDocument slots.

A slot's `validator` field names a key in DOCUMENT_VALIDATORS. The validator
runs after the basic upload checks (size, extension, detail) have passed and
receives either the uploaded file or the submitted url:

    fn(project_uploaded_document, uploaded_file=None, document_url=None) -> ValidationResult

Rejection messages live in
appl/templates/appl/include/document_validation_errors/<key>.html.
See docs/uploaded-documents.md.
"""
import logging

from appl.document_validators import tcasfolio
from appl.document_validators.base import ValidationResult

logger = logging.getLogger(__name__)

MISCONFIGURED = 'misconfigured'
VERIFICATION_ERROR = 'verification_error'

DOCUMENT_VALIDATORS = {
    'tcasfolio': tcasfolio.validate,
}


def run_document_validator(project_uploaded_document, uploaded_file=None, document_url=None):
    key = project_uploaded_document.validator
    if not key:
        return ValidationResult.accept()

    validator = DOCUMENT_VALIDATORS.get(key)
    if validator is None:
        logger.error('unknown document validator %r on ProjectUploadedDocument %s',
                     key, project_uploaded_document.id)
        return ValidationResult.reject(MISCONFIGURED)

    try:
        if uploaded_file is not None:
            uploaded_file.seek(0)
        return validator(project_uploaded_document,
                         uploaded_file=uploaded_file,
                         document_url=document_url)
    except Exception:
        logger.exception('document validator %r failed on ProjectUploadedDocument %s',
                         key, project_uploaded_document.id)
        return ValidationResult.reject(VERIFICATION_ERROR)
    finally:
        if uploaded_file is not None:
            uploaded_file.seek(0)
