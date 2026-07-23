from datetime import date, timedelta
from .c40 import c40

__doc__ = "2D-Doc header representation"
__all__ = ["Header"]

EPOCH = date(2000, 1, 1)

def date_parse_text(code):
    if code == "FFFF":
        return None
    return EPOCH + timedelta(days = int(code, 16))

def date_parse_bin(code):
    if code == b"FFFF":
        return None
    v = int.from_bytes(code, "big")
    return date(year = v % 10000,
                month = v // 1000000,
                day = (v // 10000) % 100)

def date_encode(d, mode = "c40"):
    if mode == "c40":
        if d == None:
            return "FFFF"
        return f'{(d - EPOCH).days:04X}'
    elif mode == "bin":
        if d == None:
            return b"FFFF"
        v = d.month * 1000000 + d.day * 10000 + d.year
        return v.to_bytes(3, 'big')
    else:
        raise ValueError(mode)

class Header:
    """
    2D-Doc header
    """
    def __init__(self, version, ca_id, cert_id, emit_date, sign_date, doc_type_id, perimeter_id = '01', country_id = "FR"):
        self.version = version
        self.ca_id = ca_id
        self.cert_id = cert_id
        self.emit_date = emit_date
        self.sign_date = sign_date
        self.doc_type_id = doc_type_id
        self.perimeter_id = perimeter_id
        self.country_id = country_id

    @classmethod
    def from_code(cls, code):
        """
        Parse a header from raw data, either ascii string (C40 mode) or
        blob (binary mode). Supports all versions from 1 to 4.
        """
        if isinstance(code, str) and code[0:2] == "DC":
            version = int(code[2:4], 10)
            if not (1 <= version <= 4):
                raise ValueError("Unsupported 2D-Doc version")

            ca_id = code[4:8]
            cert_id = code[8:12]
            emit_date = date_parse_text(code[12:16])
            sign_date = date_parse_text(code[16:20])
            doc_type_id = code[20:22]
            perimeter_id = int(code[22:24]) if version >= 3 else 1
            country_id = code[24:26] if version >= 4 else "FR"

        elif isinstance(code, bytes) and code[0] == 0xdc:
            version = code[1]
            if version != 4:
                raise ValueError("Unsupported 2D-Doc version")
            country_id = c40.parse(code[2:4])
            ca_cert = c40.parse(code[4:10])
            ca_id = ca_cert[:4]
            cert_id = ca_cert[4:]
            emit_date = date_parse_bin(code[10:13])
            sign_date = date_parse_bin(code[13:16])
            doc_type_id = code[16]
            perimeter_id = int.from_bytes(code[17:19], "big")

        else:
            raise ValueError("Not a 2D-Doc")

        return cls(version = version,
                   ca_id = ca_id,
                   cert_id = cert_id,
                   emit_date = emit_date,
                   sign_date = sign_date,
                   doc_type_id = doc_type_id,
                   perimeter_id = perimeter_id,
                   country_id = country_id,
        )

    @property
    def length(self):
        """
        Actual length of header, needed to know where data starts
        """
        if self.version in [1, 2]:
            return 22
        if self.version == 3:
            return 24
        if self.version == 4:
            if self.mode == "c40":
                return 26
            return 19
        raise NotImplementedError("Unhandled version")

    @property
    def mode(self):
        """
        Actual mode of header ("c40" or "bin"). Needed to interpret
        message part of document.
        """
        if len(self.country_id) == 2:
            return "c40"
        assert len(self.country_id) == 3
        return "bin"

    def to_code(self):
        "Serialize code"
        if self.mode == "c40":
            return f"DC{self.version:02d}{self.ca_id}{self.cert_id}{date_encode(self.emit_date)}{date_encode(self.sign_date)}{self.doc_type_id}{format(self.perimeter_id, '02d') if self.version >= 3 else ''}{self.country_id if self.version >= 4 else ''}"
        elif self.mode == "bin":
            return b'\xdc\x04' \
                + c40.format(self.country_id) \
                + c40.format(self.ca_id + self.cert_id) \
                + date_encode(self.emit_date, "bin") \
                + date_encode(self.sign_date, "bin") \
                + bytes([self.doc_type_id]) \
                + self.perimeter_id.to_bytes(2, "big")

    def doc_type(self):
        "Retrieve document type definition from internal database"
        from .data_definition import c40
        return c40.doctype_get(self.perimeter_id, self.doc_type_id)
