# Opinionated per-module hexagonal generator with a plan/write split

Status: accepted (generated, pending human review)

## Context

Teams copy an old module and rename it by hand to start a hexagonal module, which spreads layering mistakes. Generic project template tools do not enforce a layer layout and their output is not tested. The generator must be deterministic, safe to run against an existing tree, and testable without touching the disk.

## Decision

Split the work into three pure steps: plan_module validates names and returns an immutable list of PlannedFile; render_tree prints that plan as a sorted ASCII tree; write_plan is the only function that touches the disk. Templates are plain strings with @PKG@, @NAME@ and @ENTITY@ placeholders and no timestamps, and the output is pinned by golden files in tests/golden. write_plan resolves the root, validates every target first (no symlinked component, parent stays inside the root, no conflicts unless force), then writes UTF-8 bytes with write_bytes so newlines are LF on every platform. Names must match a strict ASCII regex and must not be keywords or stdlib module names. All checks have size and depth limits, and one ScaffoldError class with a stable code covers every failure. The standard library is the only dependency.

## Consequences

Output is byte-stable and reviewable through the golden files, and a dry run needs no filesystem. A conflict or unsafe path aborts before any file is written. The resolve-then-write check has a TOCTOU window that is documented rather than closed. Entity derivation is heuristic (series becomes Sery), so --entity is the documented fix. Only one fixed layout is generated; other languages, user templates and adapters other than in-memory are out of scope.
