from tddoc.header import Header, date_parse_text, date_encode
from datetime import date


def test_date():
    assert date_parse_text("111E") == date(2011, 12, 31)
    assert "111E" == date_encode(date(2011, 12, 31))


def test_header02():
    c = "DC02FR0AXT4A0E840E8A01"
    h = Header.from_code(c)
    assert h.version == 2
    assert h.ca_id == "FR0A"
    assert h.cert_id == "XT4A"
    assert h.emit_date == date(2010, 3, 5)
    assert h.sign_date == date(2010, 3, 11)
    assert h.doc_type_id == "01"
    assert h.to_code() == c


def test_header03():
    c = "DC03FR0AXT4A0E840E8A0101"
    h = Header.from_code(c)
    assert h.version == 3
    assert h.ca_id == "FR0A"
    assert h.cert_id == "XT4A"
    assert h.emit_date == date(2010, 3, 5)
    assert h.sign_date == date(2010, 3, 11)
    assert h.doc_type_id == "01"
    assert h.perimeter_id == 1
    assert h.to_code() == c


def test_header04():
    c = "DC04FR0AXT4A0E840E8A0101FR"
    h = Header.from_code(c)
    assert h.version == 4
    assert h.ca_id == "FR0A"
    assert h.cert_id == "XT4A"
    assert h.emit_date == date(2010, 3, 5)
    assert h.sign_date == date(2010, 3, 11)
    assert h.doc_type_id == "01"
    assert h.perimeter_id == 1
    assert h.country_id == "FR"
    assert h.to_code() == c


def test_header04_bin():
    c = bytes.fromhex("dc047ba77b9d200f2d0a5fb3e19961b0010001")
    h = Header.from_code(c)
    assert h.version == 4
    assert h.ca_id == "FR01"
    assert h.cert_id == "12345"
    assert h.emit_date == date(1969, 6, 27)
    assert h.sign_date == date(2016, 10, 5)
    assert h.doc_type_id == 1
    assert h.perimeter_id == 1
    assert h.country_id == "FRA"
    assert h.to_code() == c
