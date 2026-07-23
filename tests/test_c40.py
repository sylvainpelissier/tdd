import pytest

from tddoc.c40 import c40, text


def test_c40_parse():
    assert c40.parse(b"\x57\xd3") == "Ab"
    assert c40.parse(b"\x7b\xa7") == "FRA"


def test_c40_format():
    assert b"\x57\xd3" == c40.format("Ab")
    assert b"\x7b\xa7" == c40.format("FRA")


def test_c40_iso():
    s = "".join(chr(i) for i in range(128))
    assert c40.parse(c40.format(s)) == s


def test_text_iso():
    s = "".join(chr(i) for i in range(128))
    assert text.parse(text.format(s)) == s


def test_parse_value_above_basic_set():
    with pytest.raises(ValueError, match="Bad encoding"):
        c40.parse(b"\xff\xff")


@pytest.mark.parametrize("char", ["\xe9", "\u20ac", "\x81", "\uffff"])
def test_format_unsupported_char(char):
    with pytest.raises(KeyError):
        c40.format(char)
