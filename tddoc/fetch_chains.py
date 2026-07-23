"""
Certificate chain downloader for 2D-Doc.

Usage:
    python -m tddoc.fetch_chains [-o DIR] [CA_NAME ...]

Downloads certificate chains from the ANTS TSL (Trust Service List)
and saves individual DER files.

If the TSL is outdated a the new TSL is dowloaded and its signature is verified.

Default output: ~/.config/tddoc/chains/
Use -o tddoc/chains to update the bundled certificates.
If no CA names are specified, downloads all available chains.
"""

import sys
import argparse
from base64 import b64decode
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.x509.oid import (
    AuthorityInformationAccessOID,
    ExtensionOID,
    NameOID,
)
from cryptography.x509.verification import (
    Criticality,
    ExtensionPolicy,
    PolicyBuilder,
    Store,
)
from datetime import datetime, timezone
from importlib.resources import files
from lxml import etree
from pathlib import Path
import requests
import xmlsec

TSL_NS = {"tsl": "http://uri.etsi.org/02231/v2#"}
TSL_DS = {"ds": "http://www.w3.org/2000/09/xmldsig#"}
HEADERS = {"User-Agent": "tddoc"}
TSL_URL = "https://pub.ants.gouv.fr/2D-DOC/V1/PRD/01_TSL/tsl_signed.xml"
TSL_ROOT = "ca_racine_antsav3_2.cer"


class ChainFetcher:
    def __init__(self, output_dir=None):
        if output_dir is None:
            output_dir = Path.home() / ".config" / "tddoc" / "chains"
        self.output_dir = Path(output_dir)
        self.tree = None

    def _load_tsl(self):
        if self.tree is None:
            tsl_path = files("tddoc.tsl").joinpath("tsl_signed.xml")
            with tsl_path.open("rb") as f:
                self.tree = etree.parse(f)
        return self.tree

    @staticmethod
    def _get(url):
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        return response.content

    @staticmethod
    def _aia_ca_issuers(cert):
        """Returns the URL of the issuer's certificate, as advertised in the cert's AIA extension."""
        aia = cert.extensions.get_extension_for_oid(
            ExtensionOID.AUTHORITY_INFORMATION_ACCESS
        ).value
        return next(
            ad.access_location.value
            for ad in aia
            if ad.access_method == AuthorityInformationAccessOID.CA_ISSUERS
            and isinstance(ad.access_location, x509.UniformResourceIdentifier)
        )

    @staticmethod
    def _tsl_version(tree):
        return int(tree.xpath("//tsl:TSLSequenceNumber/text()", namespaces=TSL_NS)[0])

    def verify_tsl(self, data):
        """
        Verify a TSL and return the certificate that signed it.
        Check the XML and the certificate chain.
        Raises if either fails.
        """
        tree = etree.fromstring(data)
        leaf = x509.load_der_x509_certificate(
            b64decode(
                tree.xpath(
                    ".//ds:Signature/ds:KeyInfo/ds:X509Data/ds:X509Certificate/text()",
                    namespaces=TSL_DS,
                )[0]
            )
        )

        ctx = xmlsec.SignatureContext()
        ctx.key = xmlsec.Key.from_memory(
            leaf.public_bytes(serialization.Encoding.DER), xmlsec.KeyFormat.CERT_DER
        )
        ctx.verify(xmlsec.tree.find_node(tree, xmlsec.constants.NodeSignature))

        root = x509.load_der_x509_certificate(
            files("tddoc.tsl").joinpath(TSL_ROOT).read_bytes()
        )
        intermediate = x509.load_der_x509_certificate(
            self._get(self._aia_ca_issuers(leaf))
        )

        # A document signing certificate carries neither a SubjectAlternativeName nor an
        # ExtendedKeyUsage, both of which the default (web PKI) end-entity profile requires.
        ee_policy = (
            ExtensionPolicy.webpki_defaults_ee()
            .may_be_present(x509.SubjectAlternativeName, Criticality.AGNOSTIC, None)
            .may_be_present(x509.ExtendedKeyUsage, Criticality.AGNOSTIC, None)
        )
        verifier = (
            PolicyBuilder()
            .store(Store([root]))
            .time(datetime.now(timezone.utc))
            .extension_policies(
                ca_policy=ExtensionPolicy.webpki_defaults_ca(), ee_policy=ee_policy
            )
            .build_client_verifier()
        )
        verifier.verify(leaf, [intermediate])
        return leaf

    def check_tsl_update(self):
        """Download the published TSL and replace the bundled one if it is newer."""
        current_version = self._tsl_version(self._load_tsl())
        data = self._get(TSL_URL)
        latest_version = self._tsl_version(etree.fromstring(data))
        print(
            f"Local TSL version is {current_version}, latest TSL version is {latest_version}"
        )

        if current_version >= latest_version:
            return

        print("Verifying new TSL signature")
        leaf = self.verify_tsl(data)
        subject_cn = leaf.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
        print(f"TSL signature verified, signed by {subject_cn!r}")

        tsl_path = Path(str(files("tddoc.tsl").joinpath("tsl_signed.xml")))
        tsl_path.write_bytes(data)
        self.tree = None
        print(f"Updated {tsl_path} to version {latest_version}")

    def available_cas(self):
        tree = self._load_tsl()
        names = tree.xpath(
            "//tsl:TSPTradeName/tsl:Name[@xml:lang='en']/text()",
            namespaces=TSL_NS,
        )
        return sorted(set(names))

    def _get_ca_cert_der(self, ca_name):
        tree = self._load_tsl()
        cert_b64_list = tree.xpath(
            """//tsl:TSPTradeName[tsl:Name[@xml:lang='en']=$ac_name]
                /ancestor::tsl:TrustServiceProvider
                /tsl:TSPServices/tsl:TSPService
                /tsl:ServiceInformation/tsl:ServiceDigitalIdentity
                /tsl:DigitalId/tsl:X509Certificate/text()""",
            ac_name=ca_name,
            namespaces=TSL_NS,
        )
        if not cert_b64_list:
            raise KeyError(f"CA {ca_name!r} not found in TSL")
        return b64decode(cert_b64_list[0])

    def _get_bundle_uri(self, ca_name):
        tree = self._load_tsl()
        uri_list = tree.xpath(
            """//tsl:TSPTradeName[tsl:Name[@xml:lang='en']=$ac_name]
                /ancestor::tsl:TSPInformation
                /tsl:TSPInformationURI
                /tsl:URI[@xml:lang='fr']/text()""",
            ac_name=ca_name,
            namespaces=TSL_NS,
        )
        if not uri_list:
            raise KeyError(f"Bundle URI for {ca_name!r} not found in TSL")
        return uri_list[0]

    @staticmethod
    def _unbundle_multipart(blob):
        """Extract individual DER certificates from a multipart bundle."""
        boundary = b"--End\r\n"
        end = b"--End--"
        blob = blob.split(end)[0]
        parts = blob.split(boundary)
        certs = []
        for part in parts:
            if part.endswith(b"\r\n"):
                part = part[:-2]
            if not part:
                continue
            header, data = part.split(b"\r\n\r\n", 1)
            header_lines = header.split(b"\r\n")
            ct = None
            for h in header_lines:
                k, v = str(h, "utf-8").split(": ", 1)
                if k.lower() == "content-type":
                    ct = v
            if ct == "application/pkix-cert":
                certs.append(data)
        return certs

    def _save_cert_der(self, der, filename):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / filename
        path.write_bytes(der)
        return path

    def fetch(self, ca_name):
        # Save CA cert
        ca_der = self._get_ca_cert_der(ca_name)
        self._save_cert_der(ca_der, f"{ca_name}.der")
        print(f"Saved CA certificate: {ca_name}.der")

        # Download and unbundle leaf certs
        uri = self._get_bundle_uri(ca_name)
        print(f"Downloading {uri}")

        response = requests.get(uri, headers=HEADERS)
        response.raise_for_status()

        cert_ders = self._unbundle_multipart(response.content)
        for der in cert_ders:
            try:
                cert = x509.load_der_x509_certificate(der)
            except ValueError:
                continue
            issuer_cn = cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
            subject_cn = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[
                0
            ].value
            filename = f"{issuer_cn}_{subject_cn}.der"
            self._save_cert_der(
                cert.public_bytes(encoding=serialization.Encoding.DER),
                filename,
            )
            print(f"  Saved: {filename}")

    def fetch_all(self):
        for ca_name in self.available_cas():
            try:
                self.fetch(ca_name)
            except Exception as e:
                print(f"Error fetching {ca_name}: {e}", file=sys.stderr)


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Download 2D-Doc certificate chains from ANTS TSL",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory (default: ~/.config/tddoc/chains/)",
    )
    parser.add_argument(
        "ca_names",
        nargs="*",
        help="CA names to fetch (default: all)",
    )
    parsed = parser.parse_args(args)

    fetcher = ChainFetcher(output_dir=parsed.output_dir)
    print(f"Output directory: {fetcher.output_dir}")
    fetcher.check_tsl_update()

    if parsed.ca_names:
        for ca_name in parsed.ca_names:
            fetcher.fetch(ca_name)
    else:
        fetcher.fetch_all()
    print("Done.")


if __name__ == "__main__":
    main()
