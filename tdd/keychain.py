from base64 import b64decode
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.x509.oid import NameOID
from importlib.resources import files
from lxml import etree
import requests

__doc__ = "Keychain management"

class KeyChain:
    """
    Certificate store, indexes certificates through common name of
    issuer and subject. This is somehow 2D-Doc specific.
    """
    def __init__(self, certs = {}, cas = {}):
        self.certs = dict(certs)
        self.cas = dict(cas)

    def lookup(self, ca_cn, cert_cn):
        name = ca_cn + cert_cn
        if name in self.certs:
            return self.certs[name]
        
        if ca_cn in self.cas:
            ca = self.cas[ca_cn]
        else:
            # Search for CA
            chains = files('tdd.chains')
            ca_file = chains.joinpath(ca_cn + ".der")
            if not ca_file.is_file():
                raise KeyError(ca_cn)
            
            with ca_file.open("rb") as fd:
                ca = x509.load_der_x509_certificate(fd.read())
                self.cas[ca_cn] = ca

        chains = files('tdd.chains')
        chain_file = chains.joinpath(name + ".der")
        if not chain_file.is_file():
            raise KeyError((ca_cn, cert_cn))
        with chain_file.open("rb") as fd:
            cert = x509.load_der_x509_certificate(fd.read())
        
        # Verify the certificate is signed by the CA
        cert.verify_directly_issued_by(ca)
        self.certs[name] = cert
        return cert 

    def der_multipart_load(self, blob):
        boundary = b"--End\r\n"
        end = b"--End--"
        blob = blob.split(end)[0]
        certs = blob.split(boundary)

        for c in certs:
            if c.endswith(b'\r\n'):
                c = c[:-2]
            if not c:
                continue
            header, data = c.split(b'\r\n\r\n', 1)
            header_lines = header.split(b'\r\n')
            ct = None
            for h in header_lines:
                k, v = str(h, 'utf-8').split(": ", 1)
                if k.lower() == "content-type":
                    ct = v
            if ct == "application/pkix-cert":
                self.save_der(data)

    def save_der(self, der, ca=False):
        try:
            cert = x509.load_der_x509_certificate(der)
        except ValueError:
            return
        
        cn_attributes = cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)
        issuer_cn = cn_attributes[0].value if cn_attributes else None
        cn_attributes = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
        subject_cn = cn_attributes[0].value if cn_attributes else None
        
        if ca:
            issuer_cn = ""

        chains = files('tdd.chains')
        name = issuer_cn + subject_cn
        chain_file = chains.joinpath(name + ".der")
        with chain_file.open("wb") as f:
            f.write(
                cert.public_bytes(
                    encoding=serialization.Encoding.DER
                )
            )
    
    def download_ca(self, ca_cn):
        ns = {"tsl": "http://uri.etsi.org/02231/v2#"}

        tsl = files('tdd.chains').joinpath("tsl_signed.xml")
        with tsl.open("rb") as f:
            tree = etree.parse(f)

        cert_b64_list = tree.xpath(
            """
            //tsl:TSPTradeName[tsl:Name[@xml:lang='en']=$ac_name]
                /ancestor::tsl:TrustServiceProvider
                /tsl:TSPServices
                /tsl:TSPService
                /tsl:ServiceInformation
                /tsl:ServiceDigitalIdentity
                /tsl:DigitalId
                /tsl:X509Certificate/text()
            """,
            ac_name=ca_cn,
            namespaces=ns
        )
    
        if len(cert_b64_list) == 0:
            print("CA not found")
            return False
        else:
            self.save_der(b64decode(cert_b64_list[0]), ca=True)
        
        return True

    def download_certs(self, ca_cn):
        tsl = files('tdd.chains').joinpath("tsl_signed.xml")
        with tsl.open("rb") as f:
            tree = etree.parse(f)

        ns = {"tsl": "http://uri.etsi.org/02231/v2#"}
        uri_list = tree.xpath(
            """
            //tsl:TSPTradeName[tsl:Name[@xml:lang='fr']=$ac_name]
                /ancestor::tsl:TSPInformation
                /tsl:TSPInformationURI
                /tsl:URI[@xml:lang='fr']/text()
            """,
            ac_name=ca_cn,
            namespaces=ns
        )
        if len(uri_list) == 0:
            print("URL not found")
        else:
            print(f"Loading: {uri_list[0]}")
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"
            }
            with requests.get(uri_list[0], headers=headers) as response:
                data = response.content
                self.der_multipart_load(data)

if __name__ == "__main__":
    import sys

    k = KeyChain()
    if len(sys.argv) < 2:
        # Test certificate
        ca_cn = "FR00"
        cert_cn = "001"
        test_chains = files('tdd.chains').joinpath('FR000001.der')
        with test_chains.open("rb") as fd:
            test_cert = x509.load_der_x509_certificate(fd.read())
        k.certs["FR000001"] = test_cert
    else:
        for name in sys.argv[1:]:
            k.lookup(name[0:4], name[4:])

    for (name, c) in k.certs.items():
        print(f"name: {name} serial number: {c.serial_number}")
