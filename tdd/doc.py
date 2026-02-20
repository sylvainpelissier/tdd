from .header import Header
from .message import C40Message
from base64 import b32decode
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature

__doc__ = """
Documentation representation.
"""

class TwoDDoc:
    """
    A 2D-Doc document
    """
    def __init__(self,
                 header, message,
                 signature,
                 signed_data = None,
                 extra = None):
        self.header = header
        self.message = message
        self.signature = signature
        self.signed_data = signed_data
        self.extra = extra

    @classmethod
    def from_code(cls, doc):
        """
        Load a 2D-Doc from its ASCII form, as outputted by a barcode reader
        """
        header = Header.from_code(doc)
        if header.mode == "c40":
            data, sign = doc[header.length:].split('\x1f', 1)
            signature = b32decode(sign+"=")
            message = C40Message.from_code(header.perimeter_id, data)
            signed_data = (doc[:header.length]+data).encode("ascii")
        else:
            raise ValueError("Binary code not supported fully yet")

        return cls(header, message, signature,
                   signed_data = signed_data)

    def signature_is_valid(self, keychain):
        """
        Check signature against given keychain. If key is not
        available, KeyError is raised.
        """
        cert = keychain.lookup(self.header.ca_id, self.header.cert_id)
        r = int.from_bytes(self.signature[:32], "big")
        s = int.from_bytes(self.signature[32:], "big")
        signature = encode_dss_signature(r, s)
        try:
            cert.public_key().verify(signature, self.signed_data, ec.ECDSA(hashes.SHA256()))
        except InvalidSignature:
            return False
        return True

