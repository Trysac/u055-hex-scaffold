# Project record

## Objective

Provide a deterministic, per-module generator for hexagonal Python code whose output is itself tested. The same name always produces the same bytes, so a team gets a working, tested starting point in one command instead of copying and renaming an old module by hand.

## Scope

- In scope: `plan_module`, `PlannedFile`, `write_plan`, `render_tree`, `ScaffoldError` and the `hex-scaffold new` and `hex-scaffold layout` CLI commands; generated code that is fully typed and uses only the standard library; golden-file tests of the output.
- Out of scope: other languages, user-supplied templates, web or database adapters, editing existing modules, and project scaffolding (whole projects are covered by tools such as cookiecutter or copier).

## Timeline

| Date | Event |
|---|---|
| 2026 | Repository created from the factory utility template. |

## Effort metrics

Measured values only; a value that has not been measured stays "pending measurement".

| Metric | Value |
|---|---|
| Tokens (input / output) | 428080 / 79724 |
| Hours (human) | pending measurement |
| Cost (USD) | 0.6873 |

## Factory run u055 (measured from API usage)

| Phase | Model | Batch | Input | Output | Cache write | Cache read | Cost (USD) |
|---|---|---|---|---|---|---|---|
| generation | claude-sonnet-5-5 | yes | 2166 | 66368 | 0 | 4246 | 0.3344 |
| fix-1 | claude-sonnet-5-5 | no | 8 | 905 | 9170 | 56848 | 0.0377 |
| audit | claude-sonnet-5-5 | no | 14 | 4821 | 39822 | 154597 | 0.1633 |
| fix-2 | claude-sonnet-5-5 | no | 6 | 2058 | 11830 | 44070 | 0.0546 |
| fix-3 | claude-sonnet-5-5 | no | 8 | 787 | 7304 | 59382 | 0.0321 |
| docs | claude-haiku-5-5 | no | 106735 | 4785 | 0 | 0 | 0.0653 |

Total: $0.6873. Prices: Anthropic list prices.
