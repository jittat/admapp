"""Minimal signature check for signed PDFs (e.g., TCASFolio portfolios).

Checks, at the current time and without revocation checks or network access:
exactly one signature, covering the whole file, cryptographically valid,
chaining to one of the given trust roots, with a signer matching the pin.
See docs/pdf-signature-verification.md.
"""
from collections import namedtuple
from io import BytesIO

from appl.pdfsignatures.profiles import get_profile, load_trust_roots

SignatureCheck = namedtuple('SignatureCheck', ['ok', 'code'])

OK = SignatureCheck(True, '')

NOT_PDF = 'not_pdf'
NOT_SIGNED = 'not_signed'
MODIFIED_AFTER_SIGNING = 'modified_after_signing'
SIGNATURE_INVALID = 'signature_invalid'
UNTRUSTED_SIGNER = 'untrusted_signer'


def reject(code):
    return SignatureCheck(False, code)


def build_validation_context(trust_roots_der):
    from asn1crypto import x509
    from pyhanko_certvalidator import ValidationContext
    from pyhanko_certvalidator.policy_decl import (CertRevTrustPolicy,
                                                   RevocationCheckingPolicy,
                                                   RevocationCheckingRule)

    no_revocation_check = CertRevTrustPolicy(
        RevocationCheckingPolicy(
            ee_certificate_rule=RevocationCheckingRule.NO_CHECK,
            intermediate_ca_cert_rule=RevocationCheckingRule.NO_CHECK))

    return ValidationContext(
        trust_roots=[x509.Certificate.load(der) for der in trust_roots_der],
        allow_fetching=False,
        revinfo_policy=no_revocation_check)


def signer_matches_pin(signing_cert, signer_pin):
    subject = signing_cert.subject.native
    return (subject.get('organization_identifier') == signer_pin['organization_identifier'] and
            subject.get('organization_name') == signer_pin['organization_name'])


def verify_pdf_signature(pdf_bytes, trust_roots_der, signer_pin):
    from pyhanko.pdf_utils.misc import PdfError
    from pyhanko.pdf_utils.reader import PdfFileReader
    from pyhanko.sign.validation import (KeyUsageConstraints,
                                         SignatureCoverageLevel,
                                         validate_pdf_signature)

    try:
        reader = PdfFileReader(BytesIO(pdf_bytes), strict=False)
        signatures = reader.embedded_signatures
    except (PdfError, ValueError, TypeError, KeyError):
        return reject(NOT_PDF)

    if len(signatures) != 1:
        return reject(NOT_SIGNED)

    status = validate_pdf_signature(
        signatures[0],
        signer_validation_context=build_validation_context(trust_roots_der),
        key_usage_settings=KeyUsageConstraints(
            key_usage={'digital_signature', 'non_repudiation'},
            match_all_key_usages=False),
        skip_diff=True)

    if status.coverage != SignatureCoverageLevel.ENTIRE_FILE:
        return reject(MODIFIED_AFTER_SIGNING)
    if not (status.intact and status.valid):
        return reject(SIGNATURE_INVALID)
    if not status.trusted:
        return reject(UNTRUSTED_SIGNER)
    if not signer_matches_pin(status.signing_cert, signer_pin):
        return reject(UNTRUSTED_SIGNER)

    return OK


def verify_with_profile(pdf_bytes, profile_name):
    profile = get_profile(profile_name)
    return verify_pdf_signature(pdf_bytes,
                                load_trust_roots(profile_name),
                                profile['signer'])
