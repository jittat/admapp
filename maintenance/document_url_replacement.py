"""Replace applicants' uploaded files with links, in one file-or-link slot.

Used by scripts/replace_uploaded_files_with_urls.py. For each
(national_id, url) update, the applicant's single document in the slot is
turned into a link document: uploaded_file moves to replaced_uploaded_file
(the file stays on disk), document_url is set, and local_document_url is
cleared so fetch_mytcasfolio_pdf.py mirrors the new link.

Applicants must have an active application to the project with the given
major selected. A document that is already a link is left alone: the same
link is reported as already done, another one as a mismatch. In TCASFolio
slots links are the same when the ids at the end match (host ignored, so
student.mytcas.com and folio.mytcas.com links to the same folio match);
elsewhere the whole urls must match.
See docs/uploaded-documents.md.
"""
from dataclasses import dataclass
from urllib.parse import urlsplit

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import transaction

from appl.document_validators import run_document_validator
from appl.models import Major, MajorSelection, ProjectUploadedDocument, UploadedDocument
from backoffice.portfolio_zips import find_project_uploaded_document
from regis.models import Applicant, LogItem

REPLACED = 'replaced'
TO_REPLACE = 'to-replace'      # dry run: would be replaced
ALREADY_DONE = 'already-done'
URL_MISMATCH = 'url-mismatch'  # a warning: the document already has another link
ERROR_NO_APPLICANT = 'error-no-applicant'
ERROR_MULTIPLE_APPLICANTS = 'error-multiple-applicants'
ERROR_NOT_IN_MAJOR = 'error-not-in-major'
ERROR_INVALID_URL = 'error-invalid-url'
ERROR_NO_DOCUMENT = 'error-no-document'
ERROR_MULTIPLE_DOCUMENTS = 'error-multiple-documents'


class SetupError(Exception):
    """The project / major / slot arguments cannot be used; nothing was done."""


@dataclass
class RowResult:
    national_id: str
    url: str
    status: str
    applicant: Applicant = None
    document: UploadedDocument = None
    old_file: str = ''
    current_url: str = ''
    message: str = ''

    @property
    def is_error(self):
        return self.status.startswith('error')

    @property
    def is_warning(self):
        return self.status == URL_MISMATCH


def check_major(project, major_number):
    if not Major.objects.filter(admission_project=project, number=major_number).exists():
        raise SetupError(f'project {project.id} has no major number {major_number}')


def is_slot_for_major(slot, major_number):
    major_numbers = slot.get_major_numbers()
    return (not major_numbers) or (major_number in major_numbers)


def describe_slot(slot):
    key = slot.document_key or '(no key)'
    return f'{key} [id {slot.id}] {slot}'


def find_slot(project, major_number, document_key=None):
    """The project's file-or-link slot shown to applicants of major_number.
    With document_key, the slot with that key (as build_portfolio_zips.py
    finds it); without it, there must be exactly one candidate."""
    if document_key is not None:
        try:
            slot = find_project_uploaded_document(project, document_key)
        except ValueError as e:
            raise SetupError(str(e))
        if not slot.is_any_document:
            raise SetupError(f'slot {describe_slot(slot)} is not a file-or-link slot')
        if not is_slot_for_major(slot, major_number):
            raise SetupError(f'slot {describe_slot(slot)} is not shown for major {major_number}')
        return slot

    candidates = [slot for slot in
                  ProjectUploadedDocument.objects.filter(
                      admission_projects=project,
                      document_type=ProjectUploadedDocument.DOCUMENT_TYPE_ANY)
                  if is_slot_for_major(slot, major_number)]
    if len(candidates) != 1:
        listed = ''.join(f'\n  {describe_slot(slot)}' for slot in candidates)
        raise SetupError(f'project {project.id}, major {major_number} has '
                         f'{len(candidates)} file-or-link slots; use --slot KEY{listed}')
    return candidates[0]


def selected_applicant_ids(project, major_number):
    """Ids of applicants with an active application to project (any round)
    that selected major_number."""
    selections = (MajorSelection.objects
                  .filter(admission_project=project,
                          project_application__is_canceled=False))
    return {s.applicant_id for s in selections
            if major_number in s.get_major_numbers()}


def check_url(slot, url):
    """'' when url is acceptable for slot, otherwise the reason."""
    max_length = UploadedDocument._meta.get_field('document_url').max_length
    if len(url) > max_length:
        return f'longer than {max_length} characters'
    try:
        URLValidator()(url)
    except ValidationError:
        return 'not a url'
    result = run_document_validator(slot, document_url=url)
    if not result.is_valid:
        return f'rejected by the {slot.validator} validator ({result.code})'
    return ''


def link_id(url):
    """The last segment of the url's path: the folio id of TCASFolio links
    (.../view-folio/<id> on folio. or student.mytcas.com, or .../_/<id>)."""
    path = urlsplit(url.strip()).path.rstrip('/')
    return path.rsplit('/', 1)[-1]


def is_same_link(slot, current_url, url):
    """Whether an existing link is the one in the update. In TCASFolio slots
    the ids at the end must match, whatever the host; elsewhere the whole
    (stripped) urls."""
    if slot.validator != 'tcasfolio':
        return current_url.strip() == url.strip()
    current_id, new_id = link_id(current_url), link_id(url)
    if not current_id or not new_id:
        return current_url.strip() == url.strip()
    return current_id == new_id


def replace_with_url(document, url):
    old_file = document.uploaded_file.name
    with transaction.atomic():
        document.replaced_uploaded_file = old_file
        document.uploaded_file = ''
        document.document_url = url
        document.local_document_url = ''
        document.save()
        LogItem.create(f'Replaced file of document id {document.id} '
                       f'({document.project_uploaded_document_id}) with url by script',
                       document.applicant)


def process_row(slot, applicant_ids, national_id, url, apply=False):
    national_id = national_id.strip()
    url = url.strip()

    def result(status, **kwargs):
        return RowResult(national_id=national_id, url=url, status=status, **kwargs)

    applicants = list(Applicant.objects.filter(national_id=national_id))
    if not applicants:
        return result(ERROR_NO_APPLICANT)
    applicants = [a for a in applicants if a.id in applicant_ids]
    if not applicants:
        return result(ERROR_NOT_IN_MAJOR)
    if len(applicants) > 1:
        return result(ERROR_MULTIPLE_APPLICANTS)
    applicant = applicants[0]

    url_problem = check_url(slot, url)
    if url_problem:
        return result(ERROR_INVALID_URL, applicant=applicant, message=url_problem)

    documents = list(slot.get_uploaded_documents_for_applicant(applicant))
    if not documents:
        return result(ERROR_NO_DOCUMENT, applicant=applicant)
    if len(documents) > 1:
        return result(ERROR_MULTIPLE_DOCUMENTS, applicant=applicant,
                      message=', '.join(str(d.id) for d in documents))
    document = documents[0]

    if not document.is_file():
        status = ALREADY_DONE if is_same_link(slot, document.document_url, url) else URL_MISMATCH
        return result(status, applicant=applicant, document=document,
                      current_url=document.document_url)

    old_file = document.uploaded_file.name
    if not apply:
        return result(TO_REPLACE, applicant=applicant, document=document,
                      old_file=old_file)
    replace_with_url(document, url)
    return result(REPLACED, applicant=applicant, document=document,
                  old_file=old_file)


def replace_files_with_urls(project, major_number, updates, document_key=None, apply=False):
    """updates: (national_id, url) pairs. Returns (slot, [RowResult]).
    Raises SetupError before touching any row."""
    check_major(project, major_number)
    slot = find_slot(project, major_number, document_key)
    applicant_ids = selected_applicant_ids(project, major_number)
    results = [process_row(slot, applicant_ids, national_id, url, apply=apply)
               for national_id, url in updates]
    return slot, results
