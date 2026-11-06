# Security notes

## Threat model

`trysac-hex-scaffold` has no network access and no runtime dependencies. Its only I/O is `write_plan`, which writes files below a caller-given root.

Defended:

- **Path escape through the plan**: every planned path is checked. Absolute paths, empty paths, components equal to `..`, components containing a backslash, a colon or a NUL character, and paths deeper than 32 components are rejected with `unsafe_path`.
- **Symlinks inside the root**: each existing path component under the root is checked with `is_symlink`; a symlinked component raises `unsafe_path` and nothing is written. Resolved parents must stay inside the resolved root.
- **Overwrites**: existing files raise `conflict` unless `force` is set; all conflicting paths are reported before any write.
- **Oversized input**: plans above 256 files, files above 1 MiB and non-UTF-8 content are rejected.
- **Hostile names**: names are validated against an ASCII regular expression with `fullmatch`, keywords, soft keywords and standard library module names are refused, so generated modules cannot shadow stdlib modules.

Not defended:

- **TOCTOU races**: the checks run before the writes, so a concurrent process that replaces a directory with a symlink in between is not detected.
- **Existing file content**: with `force`, files are overwritten without backup.
- **Permissions and ownership**: files are created with default modes; the library does not check write permission beyond what the OS reports.
- **Supply chain of the generated code**: generated code is not executed by the library; its tests are the user's responsibility.

Development hygiene: `gitleaks` runs in the local gates and in CI; `.env` files are git-ignored; Dependabot runs weekly; CI actions are pinned to major versions with minimal permissions.

Releases are published to PyPI with trusted publishing (OIDC) when available, never with a long-lived token stored in the repository.

To report a vulnerability, see [SECURITY.md](../SECURITY.md).
