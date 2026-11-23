# Founders-CIV — Consolidated Canon & Simulation Specification

**Release:** v0.18 Canon & Observatory  
**Canon consolidation date:** 5 November 2026  
**Implementation baseline:** v0.17 first-integration core, wrapped by the v0.18 observatory  
**Scope:** simulation-universe rules and operational tests. Fictional story canon may contain further specifics not yet represented in executable systems.

> **Reading rule:** A **canonical principle** is an agreed fictional-universe constraint. An **implemented rule** is code currently exercised by the release. A **provisional parameter** is a deliberately chosen value for testing; it is not canon. A **planned system** has no completed simulation implementation. These distinctions are preserved in `founders_civ/canon.py` and in the dashboard's Canon register.

## 1. Why the model exists

Founders-CIV studies how societies, ecosystems and cultures develop when individual actors pursue needs, interpret fear, learn through their own and others' experiences, form beliefs and institutions, and act within persistent physical constraints. It also serves as a fictional history generator for the universe of 100 Founders. We should be able to account for how any major outcome arose through a sequence of events rather than creating civilizations by declaring them.

The research integration uses CIV-OS / RSW as an analytic lens. **RSW** concerns the normative dimension: meaning, identity, non-negotiable values, convictions, sacred commitments, legitimacy and restraint. **PSW** concerns the instrumental dimension: logistics, technical skills, coordination, contracts, production, capacity and scale. They are *aspects* of any institution, not separate competing bureaucracies. The physical substrate (L1), capital and knowledge stocks (L1b), dual aspects (L2), and distributed governance (L3) must remain distinguishable.

**Causal standard:** a claim that belief improved farming must be backed by actual changed labor, seed use, irrigation, protection, technology, food transfers or some other auditable action. The engine must never give crops a magical productivity bonus merely because enough actors agree with a belief.

## 2. Canon tiers and implementation states

- **Established canon** — lore/mechanical constraint approved in project discussion, but not necessarily implemented.
- **Operational** — demonstrably executed by the currently packaged engine and covered by local checks.
- **Partial** — a coherent simplified model operates, while important canonical features are absent.
- **Specified** — canon described and tracked but no working subsystem yet.
- **Experimental** — algorithms, thresholds, quantities and probabilities selected for a particular experiment, subject to calibration and revision.

The release ships a machine-readable register in `founders_civ/canon.py`; each entry includes rule, status, code path and unmet requirement. The register is part of the user interface and can be inspected independently of any generated history.

## 3. Physical universe and Founders

### 3.1 The House and Wellspring

There are ultimately **100 distinct Founder actors**, each capable of individual interests, relationships, learning, and self-directed choices. The House sits on a large, otherwise sparsely developed floating island; a waterfall feeds an energy river flowing across and beneath it. The Wellspring supplies the river and House with energy from an explicit universe-boundary source. The House also receives returned energy through the ten-layer Underworld. An energy-rich fountain in the House provides nourishment; Founders may replenish themselves from the river.

The House has a large stored reserve. It emits sunlight across worlds and dimensions from funded energy, with a guaranteed baseline and an additional response to incoming energy, both limited by available reserve. Founders may control *exposure* through world-specific daylight schedules. Changing a schedule redistributes opportunity to absorb light; it does not create new energy or exempt energy from being debited from the House. The exact emission formula, minimum value and gain coefficient are **experimental** pending tests of delayed return and reserve exhaustion.

### 3.2 Founders' partners, actions, immortality and checkpoints

Each Founder begins with a randomly assigned close support partner. Their mythological archetype informs history and opportunities but is not a fixed occupation or personality. Founders can learn new practices; ambitions, abilities and social contact can generate distinct specializations. Founders may construct mortal creations, worlds, connected realms and private dimensions using energy. Founder deaths are not permanent: the Founder reappears in the House using its last updated checkpoint. Progress in skills, memory and possibly inventory since that checkpoint is lost according to future checkpoint rules. A checkpoint must be actively updated in the House. Detailed memory-copy semantics, energy requirements, death distributions and checkpoint atomicity remain **specified** rather than implemented.

These physical and actor laws are intended to be reusable across the broader fiction's species and civilizations, including Humans, Dwarfs, Elfs, Svedah, Avat, Atlanteans and Naudhr. The exact physiology, history and social order of those story-world groups are **separate species/content profiles**, not free standing assumptions baked into the engine. Their detailed cosmology and historical chronology are outside this first executable systems core.

The present executable core contains **two non-aging Founder placeholders**, one in each test world. It does not yet simulate 100 autonomous Founders, checkpoint recovery, energy drinking, world construction or actual realm transitions.

### 3.3 Worlds, realms, dimensions and Spirits

Mortal creations live on worlds and ordinarily cannot travel to the House. Worlds can belong to connected realms. Private dimensions may attach to a world/realm and may require sustained energy; underfunding can destabilize a dimension into residual matter, unstable energy or collapse. Some world materials and fruits are energy-rich enough to be useful to Founders. Worlds have regional and habitat conditions as well as a day–night schedule.

There are **six Spirit actor roles**, distinct from the general word *spirit* used in spiritual validation and Soul Arts: **Knight** (interworld envoy), **Emperor** (governance), **Assassin** (covert activity), **Castor** (research, science and preservation), **Archer** (protection and training), **Berserker** (destructive predation). Spirits have agency, age and can have relationships and descendants, including with mortal species. Their aging slows in the House or dimensions and those environments protect them from age-related death, without retroactive aging on exit. At present only Castors have a working actor profile.

## 4. Energy and materials

### 4.1 Separate accounting ledgers

**Matter and energy require separate, authoritative ledgers.** A material object must not exist twice simply because a world-level ecological table and a creature's inventory both reference it. A tree harvested from a habitat transfers matter to a felled-tree or inventory state; moving it to a storeroom changes its owner/location, not total mass. Food eaten by an animal enters body, waste, environmental detritus and appropriate energy accounts. Exact elements, stoichiometry, atmospheric exchanges and chemical binding energy require the future material/element engine.

Material has stable-state identity, location, components, mass, embodied energy and accessible energy. Work energy is a funded flow, not a free property of an object. Embodied energy, chemical fuel, usable reserves, thermal heat and sunlight are not interchangeable without a defined operation. The universe can contain much energy even when usable energy is scarce.

For a completed transaction, debited mass equals credited mass (except an explicit mass-energy conversion under nuclear rules), and debited energy plus boundary inflow equals credited energy. An unfunded or partially invalid transaction is rejected **atomically**. Current code implements one-component abstract mass and funded energy transfers; it does not yet implement chemical reactions.

### 4.2 Universal toll — only for material state changes

The universal toll is paid for each registered **state transformation**: biological growth, consumption/digestion, decay, chopping a living tree into felled wood, machining wood into lumber, crafting a shelter and so forth. Merely moving a material batch or changing ownership does not trigger a toll. Do not assess the same state change twice at both fine-grained and aggregate levels. Toll energy enters three sinks: **world**, **Underworld**, **House**, with House receiving the largest share qualitatively.

The current engine uses a **10% work toll** with **20% of toll to world, 10% to Underworld layer 0, and 70% to House**. These numerical rates are **test settings, not immutable lore**. The Underworld contains ten explicit energy layers, receives returns and eventually contributes to the House. Queued returns must not silently disappear when a layer reaches capacity; detailed transport and overflow remain specified only.

### 4.3 Stellar cycle and resource renewal

The Wellspring provides an external source; the House funds sunlight delivery. Sunlight may be stored, dispersed, or transformed into biological chemical energy through material processes. Plant growth also depends on available water, nutrients and source matter. A replenished energy reservoir cannot conjure missing nitrogen, carbon, or water. Food-web energy transfer includes less-accessible heat and waste, and the nutrients/materials follow their own recycling path.

### 4.4 Manufactured and energy-dependent material

Stable states include geological material, liquid/solid/gaseous water, living producers/consumers, dead material, manufactured goods, stored food and special Founder constructs. Some constructs are **energy-maintained**: loss of sustaining energy can cause a physically registered transition to mist, electrical discharge, residual matter, or other unstable forms. Cooking changes material state, costs work and may raise *digestible fraction* without creating additional total chemical energy. Inhalants, oils and other consumables can have species-specific effects on physiology or perception even when they do not provide nutrition. These detailed recipes and status effects remain specified.

## 5. Spatial design: overlapping, non-duplicating grids

The universe is represented at several linked scales: **element → material → local space → habitat patch → region → world → realm network**. A layer's aggregate must be a view or index into the same authoritative underlying objects; it must not independently mint extra mass, energy, or inhabitants.

Habitat patches can include forests, grasslands, wetlands, mountains and human settlements. Climate, predators, shelter, food, seasonal exposure, spatial barriers and immigration differ by patch. Animals may migrate based on remembered routes, new opportunities, family/pack membership, danger and environmental change. A route can become a tradition, fall into disuse or become harmful after a change of habitat.

In the current release the engine **tracks four named habitat patches per world**, not a continuous 2D coordinate plane. The dashboard displays an **animated, diagrammatic map**: actors' patches and ecological stocks are real engine outputs; dots and sway inside each habitat are an illustration for inspection, not a claim that exact positions or collision physics have been simulated.

## 6. Universal actor design

### 6.1 Species, lifespan and individuality

All animals and other animate creations are individual actors capable of memory and Soul Network development. Every actor needs a persistent ID, species, age, health, reserves, environment, inventory, perception, motives, relationships, memories, skills, goals and network state. Species biology constrains strength, energy capacity, efficiency, reproduction, sensory ability, habitat suitability and physical action possibilities. Skills and learned strategies determine how well those possibilities are used. Chance, disease, climate and chance encounters continue to matter.

Separate **chronological age**, **biological age**, and **learned capability**. Environmental time may differ by world/realm/dimension. Biological development does not automatically grant skill; social and practical experience produces trained behavior. Spirits and Founders have their own aging/death exceptions. The current v0.17 engine tracks age and health but not separate chronological/biological rates, fertility cohorts or generation turnover.

### 6.2 Biological and cultural evolution

Individual learning occurs within a lifetime; social traditions can be transmitted across a group or generations; biological evolution changes distributions of **inherited traits** across generations through survival and reproduction. A useful learned migration route is not inherited as a gene, although offspring can learn it from a parent. A species' local population can disappear even while the species survives elsewhere, and migration cannot guarantee rescue if habitats are inaccessible or unsuitable.

### 6.3 Species ecology and feeding behavior

The model distinguishes producers, herbivores, predators, scavengers, decomposers and omnivores. Predators should survive between meals using meaningful energy reserves and metabolically efficient idle behavior. Prey encounter, search, attack, success, recovery and feeding are separate; a capture does not automatically imply reproduction. Pack predators learn coordination, role assignment and pursuit. Stealth hunters learn concealment, ambush, grapple and burst activity. Scavengers learn carcass detection and opportunistic alternatives; decomposers consume organic detritus under appropriate conditions. The observed success of real predators varies considerably; **a 30% hunting-success figure is not a universal cap or canon parameter**.

The simulation includes provisional fictional profiles: Ridge Hound, Shadow Stalker, Meadow Grazer, Forest Browser, Carrion Bird, Ground Scavenger and Soil Fungus. Their exact metabolic and hunting values are experimental. A truly viable population ecology needs mating, offspring, age-specific mortality, territory, carrying capacity, pathogens, migration corridors and food-web feedback. Those are not all implemented yet.

### 6.4 Needs, perception, beliefs and action

An actor's need domains are **physiology, safety, belonging, esteem, and self-development**. They are concurrent motives, not an obligatory staircase. Animals express analogous needs according to their species' cognitive and social capabilities. The actor's knowledge is bounded by what it perceives or hears, and may be incorrect. It chooses from *feasible* alternatives considering costs, personal experience, perceived risks, needs, relationships, goals and conviction.

An actor may have persistent goals such as protecting kin, mastering a skill or establishing food security. Long-term plans should include stages, resources, partners and abandonment conditions. The current v0.17 choice model is mainly a one-step utility approximation with simple goals; full planning remains a partial feature.

## 7. Fear Logic, spirituality and RSW

**Fear Logic is an interpretive framework rather than a formula that always discovers one true cause.** Fear may involve anticipated loss, attraction, excitement, the desire to master a challenge, obligations, threats to identity, or the limits of values and convictions. Asking how an actor's relationship to fear shapes action is part of the model. Fear need not create avoidance.

An actor's **spiritual orientation** is the evolving relationship between needs, fears, values, interpretations, **willingness** and **capability** to take action. Conviction sets direction; willingness influences accepted sacrifice and perseverance; capability makes a proposed action possible or impossible. A powerful actor may lack commitment; a committed actor may lack resources or training.

Religion can emerge when privately held spiritual interpretations are *communicated*, interpreted by others, reinforced through shared experience, and made durable in collective meanings, values, rituals and obligations. Neither communication nor participation guarantees sincere agreement. An actor might conform because of friendship, social reward, fear of sanction or coercion. Competing interpretations can generate dissent, schism, syncretism, reform or institutional capture. A norm is not automatically beneficial because it survives.

**World truth and actor belief must remain separate.** One actor may believe that a ritual causes rain; the real weather engine need not respond. The belief may still reorganize labor, redistribute food or undermine irrigation planning. If the belief changes physical outcomes, an observable action or permitted Soul Arts mechanism must account for it.

## 8. Memories, executive schemas and Soul Networks

Action → observed outcome → remembered experience → schema integration → trained skills and Nodes is the essential developmental path. Actors can receive a source-tagged lesson without agreeing with it. Agreement does not grant practical mastery. Practical training requires relevant work, observation, practice and correction; social ties influence which lessons are available and trusted.

Soul Networks comprise intrinsic and extrinsic Nodes. The Temple/Zodiac schema organizes twelve intrinsic modes; Ascendant and Descendant nodes contribute different developmental conditions. Connected nodes can form **States**. Three or more coordinated compatible States can form a **Kingdom**; a **Nation** organizes at least four States; a **Realm** comprises at least four Kingdoms and requires an **Emperor Node**. A Nation is organizational, not just a stronger Kingdom. Particular abilities require validated spiritual commitments, vows or contracts. Ordinary Soul Arts do not routinely overload; exceptional overload concerns manipulating forces or energy vastly beyond the actor's supplied resources or control capacity.

Additional established design principles: emotional attunement and intimate trust may accelerate reciprocal access to otherwise hard-to-communicate schemas, but they do not automatically transfer trained mastery or bypass network constraints. The named State catalogue remains under revision; designs have discussed Flow, Stealth, Brace, and grouped sensory/companionship or protective States rather than a strict linear level-up ladder. A valid executive schema may serve multiple applications, but more advanced manipulations must be justified by actual understanding, practiced control, the relevant spiritual commitments and funded energy. Fear Logic is one path by which actors deepen disciplinary understanding and self-knowledge in Soul Arts.

The current engine connects some practice events to elementary skill Nodes. Full intrinsic Temple modes, contract validation, State articulation, Nations, Kingdoms, Realms, soul contagion/enchantment, and complex abilities are **specified, not currently executable**.

## 9. Social structures and knowledge flow

Individuals belong to overlapping social networks: caregivers, parents, siblings, relatives, friends, neighbors, mentors, adult role models, rivals, outsiders, partners, pack members, peers, guild associates, elders and institutions. Relationships are **directed**. An apprentice may respect a mentor without the mentor sharing equal attachment. Model familiarity, attachment, trust, respect, reliance, reciprocal support, contact frequency, shared experiences and belief compatibility separately.

Social networks govern which messages are seen, how they are interpreted, and whether actors attempt a behavior. A relative may be trusted for support but not for medicine; a hunter trusted for a dangerous route may not be trusted for moral counsel. Belief can spread through kinship, prestige, observation, repetition and evidence. Knowledge access and practical competence can become unequal across families, neighborhoods and generations. Animals may transmit hunting, migration and food-search traditions when their species supports that behavior.

The live release has static directed family, neighbor, friend, mentor and apprentice links with source-tagged learning; complex dynamic friendship, childhood caregiving, fully tracked parents and cross-generational inheritance are incomplete.

## 10. Groups, institutions and civilization

Groups form from repeated interaction, common problems, communicated understandings and negotiated obligations; membership may be multiple and contested. Institutions need observable **members**, **rules**, **resource stocks**, **operating practices**, **authority arrangements** and **continuity**. A school should arise from an instructor actually mentoring and supporting apprentices, not because a teaching counter crossed a magic threshold. An institution can grow, reform, fracture, be captured by an influential group or fail through scarce resources.

Every institution needs both **RSW** (why the members view its rules as justified) and **PSW** (how it achieves its objectives), along with governance (who makes and revises decisions). CIV-OS requires distinguishing material substrate (L1) from accumulated knowledge/tools/capital (L1b). Evaluate legitimacy, distribution of costs/benefits, concentration of power, declared versus implemented rules, feedback latency and resilience.

Potential descriptions include hollowing, rigidity, drift, calibration, capture and brittleness. These are hypotheses to investigate, not automatically awarded gameplay statuses. A religion, business or family may show normative and instrumental capabilities simultaneously. The release's food-sharing pools, pledges, shared norms and monitoring are real logged events, but independent leadership, succession, production budgets and capture are not complete.

## 11. One authoritative event system

Meaningful actions produce named events with actor, world, habitat, step, causal parent(s), and optional transaction ID. A physical event commits atomically to the material/energy ledger before it becomes an accomplished fact. Observers learn through exposure to the event, subject to their access. Memories reference event IDs; training/skill changes only result from qualifying experiences. Group and institution actions include membership, rules and resources, not an aggregate magical score.

Examples of traceable chains:

1. **Tree to shelter:** inspect tree material, chop (state transform + toll), move to inventory (transfer with no toll), mill (state transform + toll), build (state transform + toll), observe teaching, practice, update skills and habitat.
2. **Drought to governance:** water shortage → fear and personal conviction → conversations with specific sources → pledges and pooling → rule monitoring → irrigation or rationing transactions → distribution and legitimacy effects.
3. **Predator culture:** prey search → attempt → successful/failed hunt → energy outcome → memory and learning → social observation by packmates → later changed hunting choice.

The present v0.18 observatory wraps an existing integrated core and filters *displayed* events for performance. The authoritative core retains more detailed event records during a run; the dashboard export contains a selected event stream and the final audit. It is not a complete forensic replay of every low-level transaction.

## 12. Simulation time and experimental protocol

Different mechanisms require different update scales: moments for transactions and communication; days for food, energy and routine choices; seasons for migration and Founder daylight interventions; years/generations for biology, culture and institutional succession. The current test uses one day as a synthetic step and does not claim real-world chronological calibration.

The registered future test is a **2×2×2×2 factorial experiment** varying Social diversity (S), individual Fear Logic (F), collective beliefs (B), and institutional feedback (I), with **16 configurations × 30 matched seeds × 720 days = 480 planned runs**. It is *not executed* in this release. Every run must state initial conditions, shocks, observed variables, random seed, experimental parameters, and rules for rejecting a hypothesis. Favor ablations, matched seeds, hold-out worlds, and event-derived explanations over post-hoc storytelling.

Primary outcome families: physical accounting; ecological persistence; survival and health; learning and practice; relationship/provenance structure; collective commitment; true institution operation and effectiveness; resource inequality; RSW–PSW divergence; Founder reserve stability. A world may conserve energy and yet be ecologically unsustainable, and a persistent institution may be harmful.

## 13. Execution coverage for v0.18

| Domain | Status | What can be inspected now | Required future work |
|---|---|---|---|
| Physical ledgers | Operational in abstract units | House, Underworld, material/energy audits, transactions and tolls | Elemental chemistry, object IDs, material states at fine resolution |
| House/daylight | Partial | Funded sunlight and separate world exposure | Baseline minimum, reserve gain calibration, delayed Underworld routing |
| Two worlds/eight patches | Partial | Plants, soil, water, detritus and animals by habitat | Dynamic high-resolution spatial/element grids, realm travel |
| 100 Founders | Specified | Two Founder placeholders | 100 actors, pairs, creation abilities, checkpoints, resurrection |
| Species ecology | Partial | Individual species, energy, hunting, migration, scavenging, mortality | Reproduction, evolution, territories, long-term food-web equilibrium |
| Needs and goals | Partial | Need measures, choices, goals and memory history | Long-term planning and deep fear/spiritual interpretation |
| Soul Network | Partial | Practice-linked elementary Node flags | States and hierarchy, vow validation, advanced network effects |
| Social learning | Partial | Directed contacts, claims with information sources, practice | Family lineage, evolving trust, imitation across generations |
| RSW / PSW | Partial | Claimed beliefs, norms, actual pledges and rules | Innovative belief formation, dissent, coercion, multiple institutions |
| Institutions | Partial | Members, pooled food, monitors and rule-revision event counts | Governance succession, durable project budgets, capture |
| Dashboard | Operational visualization | Scrubbing, play/pause, actors, habitat, energy, institutions and events | True XY movement/animation from engine, editors and world building |
| Research protocol | Specified | Canon audit, seeded single-run outputs and test docs | Run full 480-run preregistered factorial study |

## 14. Canon decisions pending author confirmation

The following should **not** be silently turned into immutable canon: the exact toll fraction and destination split; daily energy inflow and solar gain function; species energy burn/hunt success/reproduction parameters; whether actors sense Soul Network signals biologically or through learned mental interfaces; Founder checkpoint loss and stored inventory semantics; exact duration/trigger of age protection in special dimensions; which vows validate which Soul Network operations; time-dilation rates; and the operational definition of a newly founded religious institution.

## 15. Files and authoritative sources

- `founders_civ/canon.py` — structured per-system canon register and implementation status.
- `founders_civ/core/ledger.py` — currently executable matter/energy transactions.
- `founders_civ/core/engine.py` — v0.17 integrated world and actor engine (carried forward).
- `founders_civ/observatory.py` — snapshot and event extraction without modifying mechanics.
- `founders_civ/runner.py` — executable CLI and simulation exports.
- `founders_civ/server.py`, `web/` — local dashboard API, UI and 2D playback.
- `docs/V016_INTEGRATION_BLUEPRINT.md` — architecture and required future tests.
- `archive/founders_v013_species.py`, `archive/founders_v014_rsw_experiment.py` — earlier specialized research engines; **not** automatically fused into live v0.18.
- Past user research documents: *Religion Software*, *RSW v1.2*, *The-Dual-Core-Model-Tested*, *CIV-OS-v1.1-system-patch*, and *Worldbuilding Notes* (for Soul Network conventions). Some of those are external project references, not all bundled in this portable distribution.

## 16. Rules for future releases

A new feature must have (1) a precise canonical or explicitly experimental rule, (2) state variables and ownership of data, (3) action-triggered events, (4) funded material/energy effects if physical, (5) negative and positive tests, (6) output fields visible in the dashboard, and (7) a known limitation. All cross-system conclusions must be traceable. The version register must never mark a feature **operational** merely because the UI contains a tab for it.
