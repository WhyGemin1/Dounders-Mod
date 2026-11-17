# Founders-CIV Integration Handoff: Soul Ecology v0.20 Pilot and Knowledge–Trust v0.19

**Audit date:** 2026-11-06  
**Status:** Verified source-level coexistence and experimental behavior; **NOT** a merged master simulation engine or empirical validation.  
**Input archives:** `Founders_CIV_v018_Canon_Observatory (1).zip`, `Founders_CIV_v019_Knowledge_Trust_Experimental.zip`, `Founders_CIV_v020_Soul_Ecology_Research_Pilot(1).zip`; accompanying 25-page *Founders-CIV Soul Network System: Scientific Design and Implementation Report.pdf*.

## 1. The actual source lineage

SHA-256 comparisons establish that `founders_civ/core/engine.py`, `founders_civ/core/ledger.py`, `founders_civ/canon.py`, and `founders_civ/observatory.py` are **byte-identical across all three code archives**. They derive from the same tested v0.18 physical/simulation base. The main engine does not yet execute the v0.19 knowledge system or the v0.20 Soul Ecology adapter automatically.

- **CORE-018:** physical conservation ledger; actor/world simulation; Observatory and server.
- **KTC-019:** `knowledge_architecture.py`, `k01_experiment.py`, `tr01_experiment.py`, and separate knowledge/trust research tests. `k01_experiment.py` also imports `gd01_experiment.py` (included in the compatibility candidate from the earlier GD-01 branch).
- **FSEC-019:** independent Founder, Soul, evolution/population and construct systems at `founders_civ/experimental/`.
- **CONT-020:** `run_continuity_loop.py`, a shared-ledger orchestration test, not a replacement engine.
- **SOUL-ECO-PILOT:** `soul_ecology_v021.py`, `run_soul_ecology.py`, `test_soul_ecology.py`, and seasonal hazard adapter. Its title v0.21 is a *candidate patch label*, not a finalized v0.21 release.
- **SOUL RESEARCH DOCUMENT:** comprehensive proposed cognition architecture (ACT-R/Soar, episodic vs semantic learning, procedural skill, metacognition, Soul Node evidence). **Its six-store proposal is not implemented in this pilot.**

## 2. Independently performed checks in this audit

1. Uploaded v0.20 archive unchanged: `python -m unittest discover -s tests -q` → **66 tests passed**.
2. Uploaded v0.20 archive: `python -m unittest -q test_soul_ecology test_continuity_loop` → **15 tests passed**.
3. Seasonal-hazard pilot rerun: 40 seeds × 4 arms × 12 steps = **160 seeded runs**. Baseline mean alive **6.100**, full arm **7.725**; baseline unsafe exposures **139.200**, full **124.675**; baseline migrations **0**, full **15.400**. Results reproduce the uploaded report's table.
4. No-hazard rerun: 40 × 4 × 12; all four arms mean alive **21.775**, and births/food stocks identical across arms.
5. Long-run rerun: 30 × 4 × 30 = **120 seeded runs**. **All 4 arms extinct** by the end in all seeds; this is an unresolved ecological failure, not a conservation failure.
6. Copied KTC-019 `knowledge_architecture.py` and its six associated tests into an **audit copy only**, not the original archive. `unittest discover` → **72 tests passed** (66 + 6). Separate 15 targeted pilot/continuity tests passed. **87 tests are runnable side-by-side, but their successful execution does not prove systems are coupled**.
7. Added `gd01_experiment.py`, `k01_experiment.py`, and `tr01_experiment.py` to the audit copy. Two-seed K-01 and TR-01 smoke runs completed, independently, with their earlier prototype mechanics.
8. Mass and energy residuals remained close to numerical precision in rerun: peak absolute synthetic mass error about **5.8e-12** (long-run) and energy error about **2.1e-10** (no-hazard). Physical conservation does not imply biological stability.

## 3. Scientific and engineering interpretation

- The Soul Ecology pilot demonstrates a *programmed policy-mediated* survival difference in a specific constructed hazard fixture; not that simulated animals are conscious or that the model predicts real ecology.
- Full treatment changes both access to knowledge **and the decision policy**; it is not a pure memory ablation. The baseline retains a legacy `Population.teach` method that can directly add route flags; other arms have a different teaching pathway. Comparisons of route carriers therefore mix semantics.
- The two-patch world makes the only alternative patch the safer patch whenever the actor perceives current danger. A future ≥3-patch world is needed to evaluate inference about unknown destinations. The current local danger sensor obtains hazard intensity from world truth and adds limited noise: acceptable for a *sensor* fixture, but it should be encapsulated in a perception API and validated for uncertainty so an actor never receives hidden future safety directly.
- `RouteCognition.retrieve` uses a simple recency/repetition divisor, **not a full ACT-R implementation**. It lacks explicit spacing benefits, interference, prerequisite dependencies, calibrated partial comprehension, and separate retrieval/storage strength.
- `RouteCognition.episode`, KTC `KnowledgeWorld.record`, the core `Simulation._record`, and `SoulNetwork.events` use distinct event formats. The next integration must establish one global event ID and references to the original physical transaction, not four parallel causal histories.
- The pilot has route memory and route-skill records, not the PDF's recommended six stores (episodic, semantic/schema, procedural, working context, beliefs/convictions, metacognitive confidence).
- The latest PDF's Node qualification and knowledge models are **research proposals**, not evidence of their implementation. Existing `SoulNetwork.develop_state` still relies substantially on thresholds / counts.
- Simulation time units are inconsistent: population steps model demographic/generation-like aging; core engine uses simulation days. Do not merge schedules until there is a time-unit conversion and species lifecycle design.

## 4. Controlled merger plan

**Baseline:** keep the current `core.ledger.Book`, `core.engine.Simulation`, and `observatory` authoritative, since all branches already share these files. **Merge target:** a new `MASTER` branch, not a silent reassignment of the v0.20 label.

1. Standardize `Event` with unique `event_id`, `simulation_time`, `actor_id`, `perceived_context`, `objective_action_outcome`, `transaction_ids`, and `source_event_ids`. Preserve private actor-specific information separately from engine truth.
2. Unite `knowledge_architecture.Cognition` and `RouteCognition` into one `ActorCognition` with episodic/semantic/procedural/working/belief/metacognitive stores, plus directed contextual trust. Retain all original events and label migration scripts.
3. Represent route knowledge as a typed `Claim/Procedure` with a knowledge-component prerequisite graph; instruction creates exposure/representation only, practice changes procedural competence, and Soul `practice` receives the same global event ID.
4. Add cue-dependent forgetting, partial understanding, spaced practice, interference, and parameter-calibration hooks, following the PDF's **proposals** as experimentally testable mechanisms rather than immutable canon.
5. Connect actors' intended actions through `Simulation` to `Book` ledger resolution. Make all learning outcomes depend on actual actions and available information; **do not** award physical resources directly for holding memories.
6. Preserve Founder checkpoint semantics: restore only the Founder's saved internal state, not external documents/world history/other actors' memories. Include death/rebirth and Soul State evidence regression cases.
7. Repair demographic timescales and renewal, then test 3+ habitat alternatives, misinformation, teacher reliability, unknown destination quality, and risks; use matched opportunity budgets across ablations.
8. Run unified regression and negative controls, synthetic reproducibility plus human benchmark calibration where feasible, and update canonical registers only after integration acceptance.

## 5. Research vs canon vs executable status

| Proposition | Classification |
|---|---|
| 100 Founders, House energy, checkpoint resurrection | Established intended fictional canon; partial standalone implementations |
| Conservation of physical resources and energy ledger authority | Canonical, tested in core and prototype scenarios |
| Instruction differs from skill practice; memory differs from current retrieval | Canonical design principle, partially executable |
| Soul Nodes are evidence-based coordinated capabilities, not raw XP unlocks | Proposed detailed formalization; not yet fully executable |
| ACT-R-like base activation, Soar/CLS stores, habits, metacognitive confidence | Research-motivated candidate rules; **not** complete code implementation |
| 0.17/0.018 hazard rates, memory decay 0.13, learning coefficient 0.19 | Synthetic pilot settings only; not canon, not human/animal science estimates |
| 12-step survival improvement | Reproduced inside the fixture, not an ecological or psychological generalization |
| 30-step extinction | Reproduced engineering limitation |

## 6. Local reproduction commands for the compatibility candidate

```bash
python -m unittest discover -s tests -q    # 72 tests
python -m unittest -q test_soul_ecology test_continuity_loop  # 15 tests
python run_soul_ecology.py --seeds 40 --steps 12 --out results/ecology_reproduction
python run_soul_ecology.py --seeds 40 --steps 12 --no-hazard --out results/no_hazard_reproduction
python run_soul_ecology.py --seeds 30 --steps 30 --out results/long_run_reproduction
python k01_experiment.py --seeds 2 --ticks 12 --out results/k01_smoke
python tr01_experiment.py --seeds 2 --out results/tr01_smoke
```

**Final decision:** The new uploaded pilot is technically compatible with CORE-018 and brings meaningful experimental mechanics. It should be retained as a candidate integration layer, not promoted wholesale to the master engine. The included compatibility archive is intentionally an **unmerged, coexisting-module branch**. Do not call it a complete v0.21 release or claim the experiments establish consciousness, ecological sustainability, or human behavioral validity.
