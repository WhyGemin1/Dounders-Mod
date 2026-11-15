# Founders-CIV v0.19 — Four previously specification-only systems

**Status:** isolated executable prototypes + tests; **NOT** integrated into the production v0.18 world tick or Observatory UI.  
**Predecessor:** Founders-CIV v0.18 Canon & Observatory.  
**Canon policy:** established fictional rules are preserved; numeric parameters and simplified algorithms below are *experimental*, not immutable canon.

## 1. Why these four systems belong together

These systems concern continuity at different scales:

| System | Continuity being modeled | Failure or disruption |
|---|---|---|
| Founders and House checkpoints | The same named individual across death | Unsaved experience and skills are lost |
| Soul Network hierarchy | Development of practiced cognitive/spiritual organization | Incorrect technique, insufficient resources, an explicitly broken vow |
| Biological & cultural evolution | Species and knowledge across generations | Local extinction, loss of learned traditions, genetic selection |
| Energy-maintained constructs | Persistence of special materials and spaces | Insufficient energy, structural instability, physical collapse |

Their integration is important: an enduring Founder can forget skills after an unsaved death while an apprentice retains the information; a species can culturally learn to exploit a habitat while its inherited traits change slowly; a dimension can preserve institutions while it remains funded and destroy infrastructure if its power supply fails. None of these outcomes should be pre-scripted.

## 2. System A — 100 Founders and checkpoint continuity

### Established canonical rules

* Exactly 100 distinct Founder agents begin at the House, with individualized motivations and no permanent occupational classes.
* Each has a randomly assigned close support partner. The prototype uses 50 reciprocal pairs; the canonical meaning of a "support partner" need not exclude broader relationships.
* Founders can gain skills and memories through experience, may govern or create worlds, and can replenish energy from the river/Wellspring circulation.
* A Founder must be at the House to save a checkpoint; death causes rebirth at the last saved House checkpoint, with intervening learned progress lost.
* Identity persists even when autobiographical memory is rolled back; other actors and institutions need not lose their memories of the Founder.

### Implemented prototype

`founders_civ/experimental/founders.py` implements 100 IDs, reciprocal support pairing, skills, memory histories, schema fields, nested Soul Network snapshots, explicit House checkpoint saves, death and funded rebirth. Personal inventory is **not** restored; its existing ledger material is moved to the location of death, avoiding duplication. Energy is moved from the House for rebirth; if unfunded, rebirth remains pending until an available energy source funds it.

The module does **not** physically simulate Founder bodies or the energy that created the immortal body. The optional rebirth fee (2 synthetic EU) is a test assumption, not an established rule. The "pending" state is an engineering mechanism for a temporarily underfunded process, **not** permanent death.

### Improvements to consider

1. Model the Founder as a complete universal actor (needs, fear, relationships, Soul Network, energy reserves), not a detached registry object.
2. Give each checkpoint **content-addressed versions** of memory, skills, states, and event provenance. Allow a replay to show precisely what was saved and lost.
3. Clarify whether vows, external contracts, social obligations and memories held by others survive personal memory rollback. These can remain externally binding even if the Founder forgets them.
4. Define the material accounting of death and reconstructed bodies before claiming physical conservation of resurrection.
5. Keep Founder autonomy separate from assigned archetype; let ambition, constraints, experience and social relations drive specialization.
6. Make energy drinking, world creation and support-partner interactions separately testable, all funded by the shared energy ledger.

### Falsification / acceptance tests

* Exactly 100 identities and 50 reciprocal support pairs without self-pairs.
* Checkpoint cannot be created away from House; unsaved experiences do not reappear after death.
* Inventory cannot be duplicated; the House must provide any required rebirth energy.
* A second actor's knowledge of the Founder is not erased when the Founder resets.
* Unfunded rebirth becomes pending; no negative House reserve or material created.

## 3. System B — Soul Network States, Kingdoms, Nations and Realms

### Established canonical rules

* Actions and observations are converted into experiences and memory; connected practice, executive schemas and relevant Nodes support advanced development.
* Twelve intrinsic Zodiac/Temple modes exist, with Ascendant/Descendant Nodes providing different kinds of development. The specific mode descriptions are separately canonical; **the prototype only stores modes as 0–11**, without inventing names or powers.
* **Kingdom:** at least three compatible, coordinated States.
* **Nation:** at least four States arranged as an organizational system, not simply an upgraded Kingdom.
* **Soul Realm:** at least four Kingdoms and an Emperor Node. This is not the same as an interworld geographic Realm.
* Spirit validation/vows may gate specific abilities. A vow stays valid unless an explicit breaching action occurs. Ordinary failed practice is not an overload; exceptional reality manipulation without adequate energy/control may overload.

### Implemented prototype

`founders_civ/experimental/soul.py` records practice event IDs, evidenced States, validated/explicitly broken vows, connected-State Kingdoms, organizational Nations, an evidence-gated Emperor Node, and four-Kingdom Soul Realms. Activation gives one of **success**, **safe rejection**, or **exceptional overload**. Success requires a funded energy source and debits the ledger. The provisional overload ratio is just a test threshold.

### Improvements to consider

1. Represent Nodes as a network of typed edges with causal links to experience histories, emotional states, social learning and conceptual understanding—not just a set of labels.
2. Define concrete State schemas through capabilities and behavioral conditions. State attainment must require actual developmental evidence and demonstrated coordination.
3. Let Kingdoms coordinate interacting States; let Nations organize States across contexts; avoid a single monotonic experience-point ranking.
4. Treat validation as a lifecycle of a specific vow/contract and observable clauses. A belief about fulfilling a vow does not automatically validate it.
5. Create **energy demand**, **control capacity**, and **manipulated energy** as distinct variables, and test equipment/external stabilizers.
6. Use the Observatory to draw Node networks, State dependencies, contract evidence and source memories.

### Falsification / acceptance tests

* Mere belief without practice cannot unlock a State; a broken required vow blocks activation.
* Three disconnected States do not form a Kingdom; three coordinated States may.
* Four States can form a Nation; four distinct Kingdoms plus an Emperor Node are necessary for a Soul Realm.
* The ordinary mismatch returns safe rejection without free energy or injury; only explicit extreme mismatch reports exceptional overload.
* Energy spending is funded from real ledger accounts; no free successful activation.

## 4. System C — Biological and cultural evolution

### Established canonical rules

* Every animal is an actor with biological traits, memories, learned capabilities and a Soul Network.
* Inherited biological traits influence physical capability; trained behaviors such as migration, foraging and hunting are **not encoded directly as inherited memories**.
* Social learning can transmit skills or route knowledge from parents, peers, mentors and groups; the learner still needs practice.
* Biological evolution means inherited variation across generations plus differential survival/reproduction; cultural evolution means transmission and modification of learned practices.
* Local absence does not imply global species extinction. Migration is an opportunity, not a guaranteed rescue mechanism.

### Implemented prototype

`founders_civ/experimental/evolution.py` uses individual organisms with two example inherited traits (`cold_tolerance`, `foraging_efficiency`), two habitats, inherited variation, two-parent reproduction, age, mortality, energy-funded feeding, energy-limited reproduction, migration and source-tagged route teaching. Every animal has an individual Soul Network; exposure to a route produces a practiced Node event, not genetic inheritance. Feeding, birth, and death are balanced physical transactions; movement costs energy but does not incur the material transformation toll.

**Scientific boundary:** the eight-step trial is a generational toy experiment. Fixed 1-unit bodies, coarse abstract food-to-biomass transitions, juvenile development, selection coefficients and trait meanings are not real species measurements. It does not yet calculate carrying capacity, real metabolism, mutation distributions, mate compatibility, predation or food regeneration accurately.

### Improvements to consider

1. Add **species profiles** for herd grazer, woodland browser, pack hunter, ambush predator, scavenger and decomposer; make traits physical and behaviorally learnable, not hard-coded survival odds.
2. Replace generational jumps with lifespan-scaled individual daily/seasonal updates: maturity, gestation, parenting, disease, courtship, senescence and migration.
3. Model genetics separately from epigenetic/developmental plasticity and socially transmitted information; never inherit a learned route automatically.
4. Use habitat patch and region graphs for local migration, territory, feeding access, and safe refuges; calculate **local and global** extirpation independently.
5. Incorporate parental knowledge, group traditions, social networks and Soul Arts practice into reproductive outcomes without treating cultural success as genetic change.
6. Complete trophic matter/energy recycling, population carry-over and environmental perturbations before comparing long-term biological stability.

### Falsification / acceptance tests

* A child inherits a combination of parental trait parameters, with mutation where configured, but no route memory at birth.
* A taught route has source evidence and requires a contact opportunity.
* Birth, feeding and mortality cannot create mass or accessible energy from nothing.
* Cold-selection and mild-selection counterfactuals use the same initial seeds; differences are measurable but are outcomes of explicit assumptions, not evidence about real species.
* Predators and prey must pass multigeneration survival tests under multiple environmental schedules.

## 5. System D — Energy-maintained dimensions and special materials

### Established canonical rules

* Some constructs and dimensions remain stable only while sustaining energy is supplied.
* A private dimension is tied to a host world/realm and occupies a material-energy boundary; it can collapse when sustaining input fails.
* Continued expenditure of maintenance energy is an **energy movement**, not automatically a material-state transformation and therefore must not incur the universal toll on every tick.
* Building, structural collapse and conversion to mist, residual matter or inert forms are material-state changes and pay the toll once per transition.
* No transformation deletes mass, creates usable energy, teleports mortals to the House, or automatically kills occupants without an explicit hazard mechanism.

### Implemented prototype

`founders_civ/experimental/constructs.py` builds a materialized construct or dimension from an existing material stock, funds its reserve and binding energy from House accounts, charges maintenance against its reserve, degrades stability under sustained deficits, and converts it to a tracked remnant/mist/inert state on funded collapse. A single collapse event carries its inhabitants as **unresolved hazard references**, rather than assuming they vanish or teleport. Results and energy/mass audits are reproducible.

### Improvements to consider

1. Anchor dimensions in the nested geographic world/realm graph; require legitimate creator permissions and paths.
2. Separate **energy maintenance**, **structural integrity**, **material phase**, **boundary permeability**, and **inhabitant safety** into different variables.
3. Include stored energy, waste heat, phase transition, and binding energy requirements; one collapse cannot be charged twice.
4. Introduce stabilization techniques, Soul Network abilities, repair work, backup supplies, and Founder-funded maintenance contracts.
5. Make restoration nontrivial: transformed material must be recovered and work invested; a collapsed dimension is not resurrected by simply topping up a deleted account.
6. Test collective institutions that depend on infrastructure, and track who bears collapse costs (CIV-OS cost incidence).

### Falsification / acceptance tests

* Fully funded dimensions remain stable; insufficiently funded ones degrade and, at zero integrity, transform.
* Maintenance debits funded energy but pays **no transformation toll** if the material state does not change.
* Building and collapse each pay exactly one toll; nothing is spent twice or produced for free.
* If occupants exist, the system emits a hazard requiring a separate explicit outcome; no silent actor deletion or forbidden House travel.

## 6. Cross-system operational tests recommended

| Test | Active connections | Observable mechanism |
|---|---|---|
| **Checkpoint vs collective memory** | Founder death, social memory, external contracts | Founder forgets unsaved development; others and institutions remember |
| **Soul Arts stabilize a dimension** | Soul schema, energy control, construct maintenance | Stabilization succeeds only with qualified State and funded energy |
| **Cultural rescue after local famine** | Migration, parental teaching, habitat, breeding | A route survives a generation through instruction; local population may recover |
| **Failed spiritual promise** | RSW vows, Soul validation, governance | Explicitly broken contract changes actual ability access and social legitimacy |
| **Dimension collapse and governance** | Constructs, Founder energy, institutions, material ledger | Underfunding produces auditable hazards and negotiated resource response |

Use a 1-day transactional test, then 30-day diagnostic, 120-day stress test and multigeneration sensitivity study for each coupled feature. Only after these pass should the model join the existing **16 configurations × 30 matched seeds × 720 days** registered experiment. Do not change those study factors silently to make the results come out favorably.

## 7. What remains intentionally unimplemented

The live v0.18 `Simulation.step` and 2D Observatory are **unchanged** by this prototype release. These modules do not yet produce a world with 100 independent Founder policies, physical immortal bodies, complex Soul combat, all species' life histories, interrealm travel, dimension occupancy physics or the full thermodynamic chemistry model. All four systems remain **specified-only in the v0.18 live engine** until a separate integration milestone. Their independent prototypes are now implemented and tested; that is a narrower claim.

## 8. Source and validation boundary

The starting rules were consolidated from the user's previous Founders-CIV discussions and v0.18 `founders_civ/canon.py` and `docs/CANONICAL_SIMULATION_SPEC.md`. The implementation uses `founders_civ/core/ledger.py` directly rather than duplicating physical conservation code. Earlier narrative simulations illustrate fictional mechanics, not empirical validation of actual species, societies or religion. Numeric rates and overload thresholds in the prototype are test parameters.
