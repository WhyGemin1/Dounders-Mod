# Compatibility Matrix — as audited for WORLD-024 / INTEGRATION-025

| Branch | Runs through extension host | Read-only inspection | What is not asserted |
|---|---|---|---|
| CORE-018 | Used underneath WORLD-024 | Yes via `Book.audit` | Extension-host does not replace or monkeypatch physics |
| KTC-019 | Partial cognitive structures in WORLD-024 | Only through exposed World / Founder views | Full ACT-R-style forgetting and calibrated learning not integrated |
| SOCIAL-021 | Included within WORLD-024 | Yes via `describe_branch` | Legacy `SocialSimulation` alone is not a living world |
| WORLD-022 | Shared seed/creation flow reused | Yes via `describe_branch` | A planted seed alone is not a living ecology |
| WORLD-023 | Living 4-habitat tree inherited | Yes via `describe_branch` | Not a complete biosphere or persistent institution |
| WORLD-024 | **Yes** (`IntegrationHost`) | **Yes** | Not full immutable state snapshots or production-stable plugin sandbox |
| INTEGRATION-025 | Optional add-on to WORLD-024 | n/a | No claim of new foundational ecology or real-world validation |

## Supported extension mechanisms

- Pure instrumentation: `on_event`, `on_cycle`, `report`; works now.
- Documented scenario interventions: shock windows registered *before* simulation; works now.
- Branch adapters: non-mutating `describe_branch`; works on known object types.
- New actor actions: **not** exposed by the generic extension API yet; must integrate with `IntegratedWorld._proposals/_do` in an experimental engine subclass and add physical transactions with tests.
- Persistent state migrations across major versions: **not** supported; apply a declared migration plan and run cross-version replay tests.
- Network-installed third-party code: not supported. Trusted local Python only, explicit opt-in.
