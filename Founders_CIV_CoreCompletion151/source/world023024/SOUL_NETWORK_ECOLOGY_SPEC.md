# Founders-CIV — Soul Network & Animal Ecology: Selective Integration Specification

**Version:** v0.20 compatible experimental patch / v0.21 candidate  
**Status:** runnable research adapter; not a new universe-wide canonical upgrade.  
**Date:** 2026-11-06

## Scope and non-negotiable canon

This patch changes *how animals acquire, retrieve and apply knowledge*; it does not change the fictional ontology of the Soul Network. Every animal is an actor with a Soul Network. Qualified actions and their consequences become contextual evidence for skills, schemas and Nodes. Biological genes are inherited through reproduction; acquired route knowledge is not genetically inherited. Family and social contacts may transmit knowledge but cannot transfer mastered skills automatically. A State requires coordinated Nodes and appropriate developmental evidence. Kingdoms, Nations and Realms retain established hierarchical requirements; numeric tuning is not canon. Ordinary failed activations reject safely; extreme mismatch can overload, as separately implemented in v0.20. Founder checkpoints, vows and spiritual validation are unchanged.

**Explicit boundary:** A fictional Soul Network is not a claim about actual quantum physics or an empirically demonstrated supernatural mechanism. Cognitive-science results motivate only the *information-processing rules*.

## Selected improvements from completed Deep Research

| Mechanism | Scientific rationale | Implemented in this adapter | How to validate |
|---|---|---|---|
| Source-tagged episodic memory | Episodic vs generalized knowledge; Soar episodic storage | `Episode` carries day, situation, route, observed/direct action, source, strength | Audit lineage to original event; distinguish teacher from self |
| Cue-sensitive, fallible retrieval | ACT-R/Soar recency, frequency, context; forgetting | `RouteCognition.retrieve` uses season-specific cue, recency and repetition; memories persist even when temporarily inaccessible | Old memory loses accessibility, not automatically deleted |
| Observation ≠ competence | Observational learning vs procedural acquisition | `instruct` changes route belief only; `practice` changes route skill and writes to actual `SoulNetwork.practice` | Teaching alone cannot grant a practiced Node or State |
| Prediction-driven belief revision | Prediction-error learning and metacognitive evaluation | Direct experience adjusts route quality and source trust | False directions lose confidence after contradictory evidence |
| Fear as interpreted risk / agency | RSW Fear Logic: need, fear, willingness and capability direct action | Perceived local hazard and retrieved route evidence influence migration/exploration | Travel helps in a patterned seasonal hazard, not by a hidden health bonus |
| Developmental provenance | Soul development requires connected experiences | Actual practiced migration IDs enter existing Soul Network events | No ability/State unlock from hearing a lecture |

**Not implemented**: actual ACT-R architecture, neural network dynamics, full episodic replay/consolidation, learned route planning across >2 patches, discrete habitats with individual XY positions, complex social trust networks, cross-context Node/State certification, realistic animal migration algorithms, spatially explicit resource regeneration, complete animal life histories, and RSW religious belief in animals. We specifically excluded them to keep the causal test narrow.

## Cognitive pipeline

`Objective habitat state -> imperfect local perception -> cue-based retrieval -> belief + confidence -> fear/feasibility appraisal -> choose migrate/explore/stay -> existing v0.20 movement + energy cost -> outcome -> source-tagged episode -> procedural practice + belief revision -> SoulNetwork.practice(event_id)`

- Objective danger cannot be passed directly into the actor's *destination choice*. The animal knows its **current local danger cue**, the adjacent patch's identity and whatever its own memory/social network supplied; the other patch's true safety is determined only after entering it.
- Each migration uses the unmodified v0.20 `Population.migrate` and `Book.move`, so its energy expenditure is real rather than a free cognitive bonus.
- `instruct` creates an observed procedural *template* and proposition with a source. It does not grant practical competence. A recorded practice event qualifies as evidence for a migration Node but cannot independently produce a State.
- Long-term knowledge remains as source-tagged records even if current retrieval fails. Memory accessibility is fallible and contextual.
- Historical routes acquired by a parent are **not inherited as genes**. Social teaching requires actual encounters.
- Learnable parameters remain calibration inputs, never fixed canon or guaranteed scientific values.

## Experimental fixture: unavoidable distinction

**The existing v0.20 ecology does not contain differentiated patch-level hazard.** With two similar food-stock patches, remembering a migration route offers little survival value. To test cognitive action meaningfully we add an **identical, clearly isolated seasonal habitat-hazard fixture** to all comparison arms. This is not a silent change to v0.20 biology or a permanent new ecological rule.

- Two existing patches (`north`, `south`); start with 30 `Population` grazers; 240 abstract food-mass units per patch.
- Every six engine iterations the safe patch switches. `south` is safer in the cold context; `north` in mild context.
- Additional fixture-specific daily hazard: high **0.17** in the exposed patch and low **0.018** in sheltered patch. These are **invented stress-test parameters**. The original v0.20 age cutoff, reproduction, energy budget, mutation, and feeding are not modified.
- Actors get noisy local danger perception; they do not see a magic marker on the safe destination. A direct attempt to travel uses the same ledger transaction path in every arm.
- All arms begin with equivalent two experienced elders and seasonal-route history; contact mechanisms differ by experiment design. Baseline retains original v0.20 `teach` logic; enhancements separate hearing from practicing.
- Two further controls: **no-hazard condition** checks for unjustified ecological bonuses; **30-step stress test** checks long-run persistence.

## Four arms and why each exists

| Arm | Information-processing behavior | Isolated hypothesis |
|---|---|---|
| `baseline` | Original v0.20 migration/teaching behaviors; no new fear-guided migration | Reference behavior under exactly the same hazard fixture |
| `episodic` | Own stored route information with cue-dependent retrieval, occasional exploration | Is personal memory enough? |
| `social` | Episodic + recorded social instruction and source-tagged belief | Does social information provide extra behavior? |
| `full` | Social + interpretable threat appraisal + independent exploration + practice updates | Do knowledge and agency operate together to reduce exposure? |

**Ablation caveat:** Arms differ in action-selection policies as well as availability of learning information. A survival improvement therefore supports the **combined Soul-mediated behavior** under this fixture; it cannot uniquely identify a pure memory effect or quantify benefits of spirituality in biological animals. More narrowly matched mechanism-off ablations are needed before canonizing parameters.

## Accounting and acceptance criteria

1. No effect of memory/rumors on total ledger mass/energy unless an actual physical action occurs.
2. No material-state toll from knowledge acquisition, retrieval, friendship or simple movement. Original `Book` still controls transformation tolls.
3. Stable random seeds, deterministic source-tagged event IDs, and independent cognitive versus ecological random draws to reduce incidental demographic RNG shifts.
4. A learned belief is not an inherited gene; observation is not a skill; direct, evidenced practice connects to the actual Soul Network.
5. For the no-hazard control, all treatment arms must have identical ecological results under a matched seed. Decision layers cannot award survival for simply existing.
6. Long-term extinction must be reported as a failure of demographic persistence even if all conservation tests pass.

## Source basis (science rather than fictional canon)

- McClelland, McNaughton & O'Reilly (1995), *Why There Are Complementary Learning Systems in the Hippocampus and Neocortex*. https://pubmed.ncbi.nlm.nih.gov/7624455/
- Soar cognitive architecture, *Episodic Memory*. https://soar.eecs.umich.edu/soar_manual/07_EpisodicMemory/
- Soar cognitive architecture, *Semantic Memory*. https://soar.eecs.umich.edu/soar_manual/06_SemanticMemory/
- Jesmer et al. (2018), *Is ungulate migration culturally transmitted?*. https://pubmed.ncbi.nlm.nih.gov/30190405/
- Rendell et al. (2010), *Why Copy Others? Insights from the Social Learning Strategies Tournament*. https://pubmed.ncbi.nlm.nih.gov/20378813/

## Follow-up implementation priorities

**Priority A: fix demographic collapse before calling ecology sustainable.** The existing `Population.step` advances age by one every iteration and kills individuals after age >9; reproduction and replenishment schedules are insufficient to maintain a population by step 20–30, even with abundant food. Separate ecological lifecycle mechanics from the cognitive adapter.

**Priority B: richer, falsifiable animal learning.** Add three or more habitats, paths with actual travel failure/cost, multiple imperfect teachers, misinformation and environmental change; quantify whether remembering and correcting a route is independently useful.

**Priority C: graduate from experience tracking to Node certification.** Give a migration Node explicit prerequisites: sufficient independent successes, coherent representations, and cross-context transfer. Do not use raw XP or auto-unlock States.

**Priority D: Observatory linkage.** Visualize an animal's decision replay as observation -> retrieved route/teacher -> fear appraisal -> migration -> outcome -> new episode/Node evidence; preserve objective truth and subjective belief as separate displays.
