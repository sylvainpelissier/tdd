from cryptography import x509
from cryptography.x509.oid import NameOID
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

__doc__ = "Keychain management"

USER_CHAINS_DIR = Path.home() / ".config" / "tddoc" / "chains"

MULTIPART_BOUNDARY = b"--End"


class ExpiredCertificateError(Exception):
    """Raised when a certificate has expired or is not yet valid."""

    pass


class KeyChain:
    """
    Certificate store, indexes certificates through common name of
    issuer and subject. This is somehow 2D-Doc specific.
    """

    def __init__(self, check_expiry=True):
        self.certs = []
        self.check_expiry = check_expiry

    @staticmethod
    def _cn(name):
        """Extract common name from an x509 Name."""
        attrs = name.get_attributes_for_oid(NameOID.COMMON_NAME)
        return attrs[0].value if attrs else None

    def lookup(self, ca_cn, cert_cn):
        """
        Find a certificate by CA and subject common names.
        Verifies the certificate is signed by the CA before returning.
        Raises KeyError if certificate or CA not found.
        Raises ExpiredCertificateError if check_expiry is True and
        the certificate is expired or not yet valid.
        """
        cert = None
        ca = None
        for c in self.certs:
            subject_cn = self._cn(c.subject)
            issuer_cn = self._cn(c.issuer)
            if issuer_cn == ca_cn and subject_cn == cert_cn:
                cert = c
            if subject_cn == ca_cn:
                ca = c
            if cert is not None and ca is not None:
                break

        if cert is None:
            raise KeyError((ca_cn, cert_cn))

        if ca is not None:
            cert.verify_directly_issued_by(ca)

        if self.check_expiry:
            now = datetime.now(timezone.utc)
            if now < cert.not_valid_before_utc:
                raise ExpiredCertificateError(
                    f"Certificate {cert_cn} not yet valid "
                    f"(valid from {cert.not_valid_before_utc})"
                )
            if now > cert.not_valid_after_utc:
                raise ExpiredCertificateError(
                    f"Certificate {cert_cn} expired "
                    f"(expired {cert.not_valid_after_utc})"
                )

        return cert

    def der_multipart_load(self, fd):
        boundary = b"--End\r\n"
        end = b"--End--"
        blob = fd.read()
        blob = blob.split(end)[0]
        certs = blob.split(boundary)

        for c in certs:
            if c.endswith(b"\r\n"):
                c = c[:-2]
            if not c:
                continue
            header, data = c.split(b"\r\n\r\n", 1)
            header_lines = header.split(b"\r\n")
            ct = None
            for h in header_lines:
                k, v = str(h, "utf-8").split(": ", 1)
                if k.lower() == "content-type":
                    ct = v
            if ct == "application/pkix-cert":
                self.der_add(data)

    def der_add(self, der):
        try:
            cert = x509.load_der_x509_certificate(der)
        except (ValueError, Exception):
            return
        self.certs.append(cert)

    def load_der_blob(self, data):
        """Load a DER blob, auto-detecting multipart vs individual certificate."""
        if MULTIPART_BOUNDARY in data:
            self.der_multipart_load(BytesIO(data))
        else:
            self.der_add(data)

    def load_dir(self, directory):
        """Load all .der files from a directory (Path or importlib Traversable)."""
        for entry in sorted(directory.iterdir(), key=lambda e: e.name):
            if not entry.name.endswith(".der") or not entry.is_file():
                continue
            with entry.open("rb") as f:
                self.load_der_blob(f.read())


def internal(include_test=False, check_expiry=True):
    """
    Spawn a keychain with all built-in certificates loaded,
    then load any user-provisioned certificates from ~/.config/tddoc/chains/.

    If include_test is True, also load the FR00 test/spec CA certificate.
    If check_expiry is False, skip validity period checks on lookup.
    """
    from importlib.resources import files

    k = KeyChain(check_expiry=check_expiry)
    chains = files("tddoc.chains")

    for entry in sorted(chains.iterdir(), key=lambda e: e.name):
        if not entry.name.endswith(".der") or not entry.is_file():
            continue
        if not include_test and entry.name.startswith("FR00"):
            continue
        with entry.open("rb") as f:
            k.load_der_blob(f.read())

    if USER_CHAINS_DIR.is_dir():
        k.load_dir(USER_CHAINS_DIR)

    return k


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        k = internal()
    else:
        k = KeyChain()
        for fn in sys.argv[1:]:
            k.load_der_blob(Path(fn).read_bytes())

    for c in k.certs:
        print(k._cn(c.issuer), k._cn(c.subject))
