__doc__ = "2D-Doc dumper helper"

def dump(doc, keychain = None):
    from .doc import TwoDDoc
    from .data_definition import c40
    d = TwoDDoc.from_code(doc)

    print("Version:", d.header.version)
    print("Country:", d.header.country_id)
    print("CA:", d.header.ca_id)
    print("Cert:", d.header.cert_id)
    print("Emit date:", d.header.emit_date)
    print("Sign date:", d.header.sign_date)
    if d.header.perimeter_id not in c40.perimeters:
        print("Perimeter:", d.header.perimeter_id)
    dt = d.header.doc_type()
    print("Emitter doc type:", dt.emitter_type)
    print("User doc type:", dt.user_type)

    last_group = None
    for m in d.message.dataset:
        if m.group != last_group:
            print(m.group.name)
            last_group = m.group
        print(f"  {m.definition.name}:", m.value)

    print("Sign:", d.signature.hex())

    if keychain:
        try:
            if d.signature_is_valid(keychain):
                print("Signature OK")
            else:
                print("Signature broken")
        except KeyError as e:
            print("Key not found:", e)

if __name__ == "__main__":
    import argparse
    from .keychain import internal

    parser = argparse.ArgumentParser(description="Dump 2D-Doc content")
    parser.add_argument("files", nargs="+", metavar="code.txt",
                        help="2D-Doc text files to dump")
    parser.add_argument("--test-ca", action="store_true",
                        help="Load FR00 test CA certificate")
    args = parser.parse_args()

    keychain = internal(include_test=args.test_ca, check_expiry=not args.test_ca)

    for fn in args.files:
        with open(fn, 'r') as fd:
            blob = fd.read().strip()
        print(f"{fn}:")
        dump(blob, keychain)
        print()
