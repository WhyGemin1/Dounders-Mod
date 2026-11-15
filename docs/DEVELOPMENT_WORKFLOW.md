# GitHub-first hourly development workflow

**Single authoritative workspace:** `WhyGemin1/Dounders-Mod`. `main` is protected by review convention: use a branch and draft PR; never auto-merge. This file defines *process*, not evidence that code has been integrated.

## Current priority: repository source/data organization (ORG01)

Until the repository contains a validated source-of-truth build, prioritize:
1. **Inspect:** fetch default branch SHA, file tree, existing open PRs, manifests, newest verified source archive and actual `cycle_state.json`.
2. **Classify:** source vs tests vs contracts vs sample data vs runtime snapshots vs generated artifacts vs archives, with exact paths and hashes.
3. **Consolidate safely:** implement one tangible migration per hourly run on an experimental branch; retain original paths as necessary for backward compatibility. Do not upload unknown binaries/secrets to this public repo.
4. **Validate:** run actual import/build/pytest/unittest checks when executable tools exist; otherwise mark `NOT RUN` and hold code migration in draft.
5. **Persist:** branch, commits, PR, artifact links, source hashes, tests and next task in `docs/cycle_state.json` and append-only `docs/DEVELOPMENT_LEDGER.md`. Re-read state from GitHub at start; Google Drive is backup reference, not authoritative source control.

## Three-run lock after organization

Maintain the existing 3-completed-invocation cycle per mechanic (slice → integration → validation), starting from M01 only when actual sources support resumption. While organizing, track `ORG01` instead of pretending the M01 integration gate is complete. M01's prior repair/validation state stays recorded and resumes after ORG01 closes.

- M01: one World Tree↔WorldBox resource gateway with one Book. External game side effects remain unverified.
- M02: autonomous Founder stewardship/harvesting decisions.
- M03: persistent Creation needs, reproduction and inheritance.
- M04: Spirits with constrained autonomy and funded actions.
- M05: knowledge and Soul Network improving decisions, not energy creation.
- M06: collective specialization/governance/trade/conflict.
- M07: habitat construction, migration, succession, disasters and realms.

## Per-cycle completion contract

Deliver one **actual GitHub change** where authorized, e.g. a verified source inventory, a migration script with tests, a runnable source import, CI smoke workflow, or a reviewed deduplication proposal. Document how it helps future implementation. No report-only churn if executable source changes are feasible.

Report: repository and base/head commit; changed paths; migration or source fingerprint; tests **executed** vs **not run**; Book authority impact; distinction between headless and in-game; honest VERIFIED/PROVISIONAL/BLOCKED classification; concrete next GitHub change. Preserve failure and unknowns.

## Mandatory safety

- Never write into `main` directly or merge without review.
- Never invent WorldBox API signatures, compile status or in-game results.
- Do not mistake `Founders_CIV_WorldBox_M01/` read-only identity bridge for later M01 Book gateway repair chain.
- Preserve time as measurement, no magical energy gains, canonical 100 Founder identities and four habitat condition.
- Existing tracked ZIPs, SQLite, DLLs, `pyc` and checkpoints must not be deleted/reorganized en masse without explicit reviewed proof of compatibility/licensing.
- A public GitHub repository is not suitable for private save data or unlicensed game assets.
