# GitHub-first development ledger (append-only)

## ORG01 — cycle 1 — 2026-11-15
- Source: `WhyGemin1/Dounders-Mod`, `main` at `26a02ba50a53770b14eae0368315ea01036d0b3c`.
- Verified access: read/write GitHub connector; recursive Git tree inspection returned 147 entries.
- Finding: live Python + C# source trees coexist with raw archives, compiled DLL references, build output, Python bytecode, SQLite and large JSON snapshots. These are tracked in Git; no bulk move or deletion has been made.
- Manifest finding: M05 `MANIFEST.json` calls C# compiled=false, game tested=false and Book-integrated=false. An additional 0.5.3 repair README exists; no fresh compile or in-game test was run in this cycle.
- Action: added repository navigation, data catalog, GitHub-first workflow and explicit cycle state on an experimental branch. `main` unchanged; no source modules modified.
- Tests: repository tree and selected text files read; build/engine/unit/ecological/WorldBox tests NOT RUN. No Book audit or claimed ecological improvement.
- Caveats: M01 identity bridge directory differs from the later Book gateway M01 experimental cycle sequence. The public repository contains historical binary/data artifacts requiring review.
- Decision: keep ORG01 active until actual source import and reproducibility are established. Prior M01 repair cycle remains experimental, not accepted or restarted.
- Next task: create an audited, **runnable** Core151/Cycle152 source import branch, document test commands and source hash, and use CI only after dependencies are verified.
