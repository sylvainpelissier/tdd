from tddoc.message import C40Message


def test_numeric_client_number_is_not_reparsed_as_phantom_field():
    """Regression: field 19 ("Numéro de client") with a purely numeric value.

    Per 2D-Doc v3.3.x, fields 18/19/1A/1B accept [A-Z][0-9]. When the value
    is numeric (e.g. "10510899") the digits must be consumed as the field 19
    value. With the old [A-Z ]-only typing the regex matched nothing, the
    digits stayed in the stream and "10" was misread as a second field 10
    (Identité) -- a phantom duplicate.
    """
    msg = C40Message.from_code(1, "1910510899")

    ids = [d.definition.id for d in msg.dataset]
    assert ids == ["19"], f"unexpected phantom field(s): {ids}"
    assert msg.dataset[0].value == "10510899"
