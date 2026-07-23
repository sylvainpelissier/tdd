"""
Tests for ChainFetcher.verify_tsl signature verification.
"""
import pytest
import xmlsec
from base64 import b64decode
from importlib.resources import files
from pathlib import Path

from cryptography import x509
from cryptography.x509.oid import NameOID
from tddoc.fetch_chains import ChainFetcher, TSL_DS

# The intermediate certificate that verify_tsl would otherwise fetch over the
# network from the leaf's AIA caIssuers URL, bundled so the tests stay offline.
INTERMEDIATE = Path(__file__).parent / "tsl_fixtures" / "intermediate.cer"


@pytest.fixture
def tsl_data():
    """The bundled, correctly signed TSL as raw bytes."""
    return files("tddoc.tsl").joinpath("tsl_signed.xml").read_bytes()


@pytest.fixture
def offline_fetcher(monkeypatch):
    """A ChainFetcher whose network fetch returns the bundled intermediate cert."""
    fetcher = ChainFetcher()
    monkeypatch.setattr(fetcher, "_get", lambda url: INTERMEDIATE.read_bytes())
    return fetcher


def test_verify_tsl_valid_signature(offline_fetcher, tsl_data):
    """A correctly signed TSL verifies and returns its signing certificate."""
    leaf = offline_fetcher.verify_tsl(tsl_data)

    assert isinstance(leaf, x509.Certificate)
    subject_cn = leaf.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
    assert subject_cn == "ANTS CACHET 2DDOC"


def test_verify_tsl_tampered_signature(offline_fetcher, tsl_data):
    """Tampering with signed content makes signature verification fail."""
    tampered = tsl_data.replace(
        b"<tsl:TSLSequenceNumber>", b"<tsl:TSLSequenceNumber>9", 1
    )
    assert tampered != tsl_data  # guard against a silently ineffective edit

    with pytest.raises(xmlsec.VerificationError):
        offline_fetcher.verify_tsl(tampered)
