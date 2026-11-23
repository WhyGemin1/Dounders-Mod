# Founders–CIV / Relational Software: Knowledge, Trust and Cognition Canon v0.19

**Adopted design specification — 6 November 2026.** This canonizes architectural rules, not empirical claims or a fully integrated physical-engine implementation. Numerical coefficients in the experiments are provisional and not canonical.

## 1. Core ontology

Relational Software comprises six coupled components: **actions, capabilities, memory, thoughts/ideas, attitudes, goals**. Knowledge is not a seventh component. It is distributed across the world, external representations, cognition, relationships and culture. An actor's beliefs and memories are not identical to the world's authoritative state. No single knowledge score represents possession, access, understanding or capability.

## 2. Seven layers

1. **World facts**: actual events and constraints established by the simulation's physical authority.
2. **Information artifacts**: records, books, archives, maps, digital documents and inscriptions; storage has material and access constraints.
3. **Personal memory**: retained, reconstructed or forgotten experiences and information, including procedural and declarative aspects.
4. **Communication**: speech, teaching, demonstration, testimony, writing and imitation; transmission is a process rather than proof of learning.
5. **Cognition**: attention, perception, retrieval, interpretation, evaluation, imagination, planning, metacognition and learning.
6. **Culture**: shared and reproduced norms, traditions, rituals, practices and institutions; persistence requires actual transmission and participation.
7. **Potential and unknown**: discoverable but unencountered information, inaccessible information, and not-yet-articulated inventions. Discovery requires investigation or reasoned generation and subsequent domain-appropriate validation.

## 3. Claims and evidence

Claims and procedures have stable IDs, subjects, representations, sources, provenance, dependencies and evidence. The registry may contain incorrect claims. Actor-specific relations to claims separately record exposure, recall, understanding, belief/confidence, practice/application, and evidence history. These dimensions are not mandatory stages. Understanding need not imply agreement; belief need not imply understanding; success need not prove an explanation is true. External records are not automatically known by actors.

## 4. Trust

Trust is actor-to-actor, directional, contextual and evidence-sensitive. Distinguish perceived **ability**, **benevolence**, **integrity**, uncertainty, reliance stakes, and actual performance. Trust is neither the same as affection nor the same as factual accuracy. Inference about another actor's intentions is fallible. Failure can result from constraints rather than dishonesty. Actors can be trustworthy yet distrusted or untrustworthy yet trusted. The experimental trust module uses separate evidence counters for ability, benevolence and integrity; these are not universal calibrated psychological measures.

## 5. Cognitive process and embodiment

The simulation uses a closed loop: environment/social context -> bounded perception and access -> cognition across the six components -> intended action -> feasibility/physical resolution -> experienced and interpreted feedback -> updated memory, attitudes, goals and capabilities. Routine/habitual and reflective/deliberative decisions may differ. Cognitive coordination is a testable functional hypothesis, not a demonstration of consciousness.

## 6. Causal tracing and research standards

All changes to knowledge and trust should reference event IDs and upstream evidence where feasible. Record both objective event outcomes and actor-perceived reports. Distinguish programmatic causal dependencies from causal claims about real people. Controlled experiments require matched seeds, independently repeated runs, explicit interventions, ablations, uncertainty, alternative baselines, and predefined failure criteria. Saturation at maximum scores is a diagnostic weakness, not a scientific success.

## 7. Implementation register

- `knowledge_architecture.py`: **experimental implementation** of claims, representations, cognitive relations, directional trust evidence, encounter/practice events and provenance.
- `k01_experiment.py`: **executed synthetic pilot** comparing direct observation, archives, speech, imitation and independent discovery using v0.18 Agent + GD-01 Founder initialization.
- `tr01_experiment.py`: **executed synthetic pilot** of reliable/unreliable source evidence and verification under different metacognition assumptions.
- `tests/test_knowledge_architecture.py`: **automated invariants** for exposure/application separation, feasibility, trust, provenance and registry integrity.
- Existing v0.18 physics/ledger, Founders' checkpoint resurrection, durable artifacts, realistic cultural institutions, learning dynamics, and consciousness: **not integrated or demonstrated by these experiments**.

## 8. Interpretation boundaries

K-01 and TR-01 are synthetic, parameterized demonstrations of code behavior. Their differences are partly caused by chosen coefficients and exposure opportunities. They do not validate the RSW six-component ontology, real-world trust, or consciousness. A future release should couple the architecture to the authoritative v0.18 material ledger and evaluate it against external observations.
