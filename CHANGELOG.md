# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3]

### Added
- Support for the latest 2D-Doc specification 3.3.8 document types.
- HTTP headers when fetching certificate chains to avoid `403` errors.
- Update to latest TSL list and verify signature when fetching certificates.
- Rename the module to tddoc

### Changed
- Fields `18`/`19`/`1A`/`1B` are now typed as alphanumeric (`StringAZ09Sp`).
- Updated internal CA certificates.
- Switched the build system to the `uv` build backend (`pyproject.toml`).

### Fixed

