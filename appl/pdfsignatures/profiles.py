"""PDF signature verification profiles and their bundled trust roots.

A profile says which root CAs a signature must chain to and which
organization must be the signer. Root certificates live in trust_roots/ and
are pinned by SHA-256 here; see docs/pdf-signature-verification.md.
"""
import base64
import hashlib
import os
import re

TRUST_ROOTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               'trust_roots')

TCASFOLIO = {
    'roots': [
        ('thailand-nrca-g1.pem',
         '2A8DA2F8D23E0CD3B5871ECFB0F42276CA73230667F474EEDE71C5EE32CC3EC6'),
        ('thailand-nrca-g3.pem',
         '3D2794A0539486A83E8032CF14FE886553E52239CBAEC1B9CFEF5595ADBBF444'),
    ],
    'signer': {
        'organization_identifier': 'TIN-0993000086848',
        'organization_name': 'Association of The Council of University Presidents of Thailand',
    },
}

PROFILES = {
    'tcasfolio': TCASFOLIO,
}

PEM_CERTIFICATE_RE = re.compile(
    rb'-----BEGIN CERTIFICATE-----\s*(.+?)\s*-----END CERTIFICATE-----',
    re.DOTALL)


class TrustRootError(Exception):
    pass


def pem_to_der(pem_bytes):
    blocks = PEM_CERTIFICATE_RE.findall(pem_bytes)
    if len(blocks) != 1:
        raise TrustRootError('expected exactly one certificate, found %d' % len(blocks))
    return base64.b64decode(b''.join(blocks[0].split()), validate=True)


def load_trust_root(filename, sha256_fingerprint, roots_dir=TRUST_ROOTS_DIR):
    """Returns the DER bytes of a bundled root, raising TrustRootError when
    the file's SHA-256 does not match the pinned fingerprint."""
    with open(os.path.join(roots_dir, filename), 'rb') as f:
        der = pem_to_der(f.read())

    actual = hashlib.sha256(der).hexdigest().upper()
    if actual != sha256_fingerprint.upper():
        raise TrustRootError('fingerprint mismatch for %s: expected %s, got %s'
                             % (filename, sha256_fingerprint, actual))
    return der


def get_profile(name):
    try:
        return PROFILES[name]
    except KeyError:
        raise TrustRootError('unknown signature profile: %s' % name)


def load_trust_roots(profile_name, roots_dir=TRUST_ROOTS_DIR):
    profile = get_profile(profile_name)
    return [load_trust_root(filename, fingerprint, roots_dir)
            for filename, fingerprint in profile['roots']]
