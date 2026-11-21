# Founders-CIV WORLD-022 — The Sea / Seed-Built Universe

Experimental integrated Founder–World application based on the latest uploaded SOCIAL-021 archive. The legacy v0.18 ecological engine and universal `Book` are preserved. This package adds a WORLD-022 integration scheduler, a seeded blueprint/creation system, 96 verified stress interventions, and a local Python-backed visual world.

## Play the living world

**Windows:** unzip the archive, open the `Founders_CIV_v020_Soul_Ecology_Pilot` folder, then double-click `START_FOUNDER_WORLD.bat`. Your browser opens `http://127.0.0.1:8765`.

**macOS / Linux:** in the extracted directory run `python3 launch_founder_world.py --port 8765 --seed 400` and open `http://127.0.0.1:8765/`.

No pip installs are needed for the runtime: the Python engine and HTTP server use the standard library, and the browser UI is one self-contained HTML file. The application runs entirely on your computer and binds only to localhost. Stop it with Ctrl+C. The DOCX files were created separately using python-docx.

## Basic creation tutorial

1. Choose Founder F001, select **Realm / island**, write a name, choose a location in the Sea (click the map to set X/Y), adjust the operating blueprint sliders, and click **Record seed blueprint**. This is an information record, not yet a physical island.
2. Click **Research** with the author selected. **Advance one cycle**, then research again if the Founder has not already researched it autonomously. The engine requires at least two different research cycles.
3. Select a different Founder **at the same site as the author**, then click **Peer review**. A review checks prerequisites and internal compatibility, not perfect scientific truth.
4. Reselect the **author** and click **Plant seed**. Planting requires available Founder energy, House energy, soil substrate, and paid transformation work. If short on energy, return to the House or visit the riverbank and click **Draw river / House energy**.
5. Select **World / tree**. Choose the new realm as its parent, follow the same blueprint/research/review/plant sequence. Then select **Underworld / flower** and choose the world as its parent. The same system supports **Species / sprout** and **Dimension / portal**.
6. **Advance cycles**. Each planted creation consumes a finite energy reserve. Click a creation and **Fund +0.6 upkeep energy** while a Founder has energy. A realm’s collapse propagates to dependent worlds, flowers, and portals.
7. Inspect the Founder, faction/knowledge metrics, events and physical account residual; click **Export state** for a JSON snapshot.

**Note:** other Founders move and pursue their own projects during time advancement. If an author and a reviewer no longer occupy the same site, choose an accessible different reviewer or travel to a neighboring site first. The prototype only has House, Riverbank, Fields, and Ridge movement nodes, not exact Sea navigation.

## Technical architecture

```text
IntegratedWorld.step()
  ├── core.engine.Simulation.step()       [authoritative ecology, original physical Book]
  ├── SOCIAL-021 SocialSimulation.step()  [100 Founders, factions, study, teaching, agency]
  ├── SeedRegistry.advance()              [creation upkeep and cascading collapse]
  └── Book.audit()                        [mass, energy, toll invariants]
```

The 100 Founders are represented by `FounderRegistry`; the two old ecological Founder placeholders are inactive records. The shared ledger, clock, and merged event timeline are authoritative within this experimental adapter. Core events and social events have source-specific event IDs, linked to the common clock and transaction IDs.

Seed classes and operating blueprints are defined in `founders_civ/experimental/world_integration.py`. The full seed lifecycle is enforced in Python, not only visually. The interface is `founder_world.html` and the server is `launch_founder_world.py`.

## Tests and reports

```sh
python -m unittest discover -s tests -q
python -m unittest -q test_world_integration test_soul_ecology test_continuity_loop
python run_world_stress.py --out results/world_stress
```

Recorded checks: **85/85 inherited**, **24/24 additional targeted**, **96/96 integration stressors** (12 families × 8 intervention variants). Across stressors: 272 actual integrated cycles, 198,439 physical ledger transactions, maximum |mass residual| ≈ 1.0e-11 and |energy residual| ≈ 3.29e-8 synthetic units. The stress suite stores all scenario outcomes in `results/world_stress/stressors.csv` and `summary.json`; deliberate invalid operations count as passes only when correctly rejected.

Documentation:

- `docs/WORLD_022_Implementation_and_Stress_Test_Report.docx`
- `docs/WORLD_022_Notes_Based_Potential_Adjustments.docx`

## Important limitations

- New world trees are **funded, persistent constructs**, not yet a full independent ecological `Simulation` instance. Species sprouts do not spawn actual reproducing populations. Underworld flowers do not yet process death or souls. The Sea's SVG map is a symbolic UI; exact geometry is not simulated by core physics.
- Physical material is **reallocated**, not created from energy. The one-component mass model is not elemental chemistry.
- The present social model still uses highly provisional learning, trust and decision coefficients. The old evolution prototype's population-extinction problem has not been solved.
- Stress results test software invariants and consequences of programmed rules. They do **not** validate human consciousness, social behavior, independent ecosystems, or the universe's fictional ontology.

## Version management

Label this experimental branch `WORLD-022`, not an unqualified master release. It is based on the newest supplied SOCIAL-021 archive and retains its standalone tests and demos. Merge into a canonical master only after world ecological generation, persistent institutions, trust calibration, spatial pathfinding, and full cross-system event semantics are validated.
