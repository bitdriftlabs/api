# bitdrift API

This repository contains the public-facing bitdrift API definitions.

## Licensing

First-party API definitions and tooling are licensed under
[PolyForm Strict License 1.0.0](LICENSE), a source-available license, not an open-source license.
Previously published versions retain their original licenses. Vendored components in
`thirdparty/` and `protoc-gen-validate/` retain their own licenses and notices.

Run `tools/check_license.sh` to check license text and schema headers without modifying files.
Run `python3 tools/license_header.py` to add missing headers or normalize canonical header
formatting, then rerun the check. Noncanonical first-party headers are rejected, not migrated.
Both commands accept explicit file paths.

## Documentation

For API documentation, see:

- API guide: https://docs.bitdrift.io/api-guide/
- Full API content (Markdown): https://docs.bitdrift.io/api/index.md

## Repository structure

- `src/` contains API definitions used by bitdrift SDKs and compatible control planes.
- `thirdparty/` contains vendored protobuf dependencies required for compilation.