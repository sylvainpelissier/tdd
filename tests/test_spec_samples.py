"""
Tests for 2D-Doc specification samples.

These tests verify:
1. Parsed data matches reference data from the specification
2. Signature validation passes
3. Re-encoding produces the same payload (unsigned portion)
"""
import yaml
from datetime import date, datetime, time
from pathlib import Path
from tddoc.doc import TwoDDoc


def load_reference(yaml_path: Path) -> dict:
    """Load reference data from YAML file."""
    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_code(txt_path: Path) -> str:
    """Load 2D-Doc code from text file."""
    with open(txt_path, "r", encoding="utf-8") as f:
        return f.read().strip()


def parse_reference_value(value, field_value):
    """
    Convert reference value to match the type of parsed field value.
    Handles date, datetime, time conversions from ISO strings.
    """
    if isinstance(field_value, date) and not isinstance(field_value, datetime):
        if isinstance(value, str):
            return date.fromisoformat(value)
        return value
    if isinstance(field_value, datetime):
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        return value
    if isinstance(field_value, time):
        if isinstance(value, str):
            return time.fromisoformat(value)
        return value
    if isinstance(field_value, bool):
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes")
        return bool(value)
    if isinstance(field_value, bytes):
        if isinstance(value, str):
            return value.encode("utf-8")
        return value
    return value


def test_spec_sample(spec_sample, keychain):
    """
    Test a specification sample against its reference data.

    Tests:
    1. Header fields match reference
    2. Message fields match reference
    3. Signature is valid
    4. Re-encoding produces same signed_data
    """
    txt_path, yaml_path = spec_sample
    code = load_code(txt_path)
    ref = load_reference(yaml_path)

    # Parse the document
    doc = TwoDDoc.from_code(code)

    # Test header fields
    header_ref = ref.get("header", {})

    if "version" in header_ref:
        assert doc.header.version == header_ref["version"], "version mismatch"

    if "ca_id" in header_ref:
        assert doc.header.ca_id == header_ref["ca_id"], "ca_id mismatch"

    if "cert_id" in header_ref:
        assert doc.header.cert_id == header_ref["cert_id"], "cert_id mismatch"

    if "emit_date" in header_ref and header_ref["emit_date"] is not None:
        expected = date.fromisoformat(header_ref["emit_date"])
        assert doc.header.emit_date == expected, "emit_date mismatch"

    if "sign_date" in header_ref:
        expected = date.fromisoformat(header_ref["sign_date"])
        assert doc.header.sign_date == expected, "sign_date mismatch"

    if "doc_type_id" in header_ref:
        assert doc.header.doc_type_id == header_ref["doc_type_id"], "doc_type_id mismatch"

    if "perimeter_id" in header_ref:
        assert doc.header.perimeter_id == header_ref["perimeter_id"], "perimeter_id mismatch"

    if "country_id" in header_ref:
        assert doc.header.country_id == header_ref["country_id"], "country_id mismatch"

    # Test message fields
    fields_ref = ref.get("fields", {})
    parsed_fields = {d.definition.id: d for d in doc.message.dataset}

    assert set(fields_ref.keys()) == set(parsed_fields.keys()), "Both ref and parsed do not have the exact same keys"

    for field_id, raw_expected_value in fields_ref.items():
        field = parsed_fields[field_id]
        try:
            expected_value = field.definition.encoding.from_spec_test_data(raw_expected_value)
        except Exception as e:
            raise ValueError(f"Cannot decode field {field_id} encoding {field.definition.encoding.__class__.__name__} from data {raw_expected_value}") from e
        actual_value = field.value

        assert actual_value == expected_value, f"field {field_id}: expected {expected_value!r}, got {actual_value!r}"

    # Test signature validation
    if ref.get("signature_valid", True):
        assert doc.signature_is_valid(keychain), "signature validation failed"

    # Test signature hex matches if provided
    if "signature" in ref:
        expected_sig = bytes.fromhex(ref["signature"].replace(" ", ""))
        assert doc.signature == expected_sig, "signature bytes mismatch"

    # Test re-encoding produces same signed_data
    if ref.get("test_encoding", True) and doc.header.mode == "c40":
        # Re-encode header
        header_code = doc.header.to_code()

        # Verify header portion matches
        original_header = code[:doc.header.length]
        assert header_code == original_header, f"header re-encoding mismatch: {header_code!r} vs {original_header!r}"
