"""
Pytest fixtures for 2D-Doc specification tests.
"""

from pathlib import Path

import pytest


def discover_test_cases(samples_dir: Path):
    """
    Discover all test cases by finding .txt files with matching .yaml files.
    Returns list of (txt_path, yaml_path) tuples.
    """
    test_cases = []
    for txt_file in samples_dir.rglob("*.txt"):
        yaml_file = txt_file.with_suffix(".yaml")
        if yaml_file.exists():
            test_cases.append((txt_file, yaml_file))
    return sorted(test_cases, key=lambda x: str(x[0]))


def pytest_generate_tests(metafunc):
    """
    Dynamically generate test cases from samples directory.
    """
    if "spec_sample" in metafunc.fixturenames:
        samples_dir = Path(__file__).parent / "spec_samples"
        test_cases = discover_test_cases(samples_dir)

        ids = [str(txt.relative_to(samples_dir.parent)) for txt, _ in test_cases]
        metafunc.parametrize("spec_sample", test_cases, ids=ids)


@pytest.fixture
def keychain():
    """
    Load the internal keychain with bundled certificates.
    """
    from tddoc.keychain import internal

    return internal(include_test=True, check_expiry=False)
