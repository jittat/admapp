# Bundled trust roots

Root CA certificates that PDF signatures are verified against. Each file is
pinned by SHA-256 in `../profiles.py`; loading fails if a file does not match,
so replacing a root means changing the file and the fingerprint in the same
commit. Background and decisions: `docs/pdf-signature-verification.md`.

Only root CAs belong here. Intermediates (e.g. INET CA - G1) come from the
signed PDF and are never trust anchors.

## thailand-nrca-g1.pem

- Subject: `C=TH, O=Electronic Transactions Development Agency (Public Organization), OU=Thailand National Root Certification Authority, CN=Thailand National Root Certification Authority - G1`
- SHA-256: `2A8DA2F8D23E0CD3B5871ECFB0F42276CA73230667F474EEDE71C5EE32CC3EC6`
- Valid: 2013-03-27 → **2036-03-27**
- Source: `https://www.nrca.go.th/cert/nrca/THNRCA.der` (retrieved 2026-09-13, TLS verified)
- Authenticated: SHA-256 matches Microsoft's CCADB included-roots report
  (status Included, EKUs include Document Signing).
- Used by: `tcasfolio` (the current TCASFolio signer chains to it via INET CA - G1).

## thailand-nrca-g3.pem

- Subject: `C=TH, O=Electronic Transactions Development Agency, CN=Thailand National Root Certification Authority - G3`
- SHA-256: `3D2794A0539486A83E8032CF14FE886553E52239CBAEC1B9CFEF5595ADBBF444`
- Valid: 2023-08-17 → **2043-08-12**
- Source: `https://crt.sh/?d=3D2794A0539486A83E8032CF14FE886553E52239CBAEC1B9CFEF5595ADBBF444`
  (retrieved 2026-09-13; no direct download found on www.nrca.go.th)
- Authenticated: SHA-256 matches Microsoft's CCADB included-roots report
  (status Included, EKU Document Signing).
- Used by: `tcasfolio` (bundled for future signer certificates issued under G3).
