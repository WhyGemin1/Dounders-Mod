# Founders-CIV SOCIAL-021 — Social Agency Implementation Specification

**Date:** 6 November 2026  
**Implementation state:** experimental executable orchestrator; **not** merged into `founders_civ.core.engine.Simulation.step`.  
**Source of worldbuilding requirements:** *Note Oct 11, 2026 2.pdf*, pp. 18–23, 25–27. Original 100 Founder names, offices, powers and relationships are source canon. The numerical assignments and policies below are **experimental**, not new character canon.

## Canon preserved

- 100 distinguishable Founder identities with 50 reciprocal close pairs; partners are social ties, not automatically trusted or always colocated.
- Eight historical squads of twelve plus four officer positions; squads are **initial organization**, not permanent occupations, fixed loyalties or exclusive skill sets. Actual member/office assignments in this pilot are provisional numerical placeholders, not claims about the original roster.
- Actors can learn skills outside their starting specialty. Founders have memory, thoughts/ideas, attitudes, goals, capabilities and actions; identity develops from interactions among these.
- Funded physical acts take place on one authoritative `Book` ledger, including action energy expenditure and real energy transfers during aid. No simulated action creates material or energy from a belief or score.
- Founder checkpoint restoration changes the Founder's personal skills, memory, goals, Soul snapshot and separately snapshotted cognitive record. Other Founders' memories and social judgments do **not** magically rewind.

## Executable modules

`founders_civ/experimental/social_agents.py` imports and reuses the existing `FounderRegistry`, `Book`, `KnowledgeWorld`, `Cognition` and directional `TrustRelation`. The code creates its own experimental world `SocialSimulation` and `step()` scheduler. It **does not modify the legacy core** and cannot yet simultaneously simulate full ecology or autonomous construction with the same physical world state.

Every Founder receives initial ability estimates in six learnable domains (craft, research, navigation, teaching, coordination, survival). Their `main_goal` and `secondary_goal` are drawn from mastery, research, exploration, solidarity, leadership and security. Ambition, curiosity, empathy and caution are persistent heterogeneous traits. The initial skill values, trait distributions and biases are **illustrative coefficients**.

## Decision cycle

1. Get current environment location and finite energy.
2. Sample at most four nearby interlocutors, weighted toward squad peers and partners where enabled. No contact across disjoint locations.
3. Generate feasible candidates for `practice`, `study`, `explore/move`, `aid`, `teach`, `coordinate`, `promise`, `checkpoint`, `recharge`, `reflect`, `organize`, `endorse`, `recruit`, and `rest` as available.
4. Score candidates using the current goal, ambition, social trust, target relation, effort constraints and availability. Select via a seeded stochastic policy (Gumbel random utility).
5. Charge the canonical `Book` for action effort or energy transfer, resolve the interaction, log a decision event, resolution event, relevant transaction IDs, and causal parent ID.
6. Update evidence-backed skills, source-specific knowledge states, three-dimensional directional trust and faction membership. Recalculate later choices from updated states.

`practice` changes procedural proficiency, at an ambition-sensitive diminishing rate. `study` gives exposure and partial comprehension about local information but **does not** grant procedural skill. `teach` requires spatial contact, a learned claim and a teacher; the learner gains representation/exposure rather than automatic skill. `coordinate` success depends on practiced coordination capability and a random draw, not trust alone. `reflect` can revise a persistent goal when progress on that goal has stagnated. Selecting an ambition-weighted action does not guarantee success.

## Social relationships and organizations

- Trust is **directional**. `ability`, `benevolence` and `integrity` are distinct estimates. An actor can trust another's helpfulness but doubt technical competence. The model uses the existing Beta-counter `TrustRelation` implementation.
- Assistance is a physically funded transfer and can increase *recipient-perceived* benevolence. Joint coordination can update *perceived* ability after observed success or failure.
- A promise of future help creates a dated commitment; fulfillment updates recipient-perceived integrity, and unfulfilled promises can decrease it. Nonfulfillment does not prove dishonesty or malevolent intent.
- A faction begins as a **proposal** known only to invited actors. It becomes a formed institution only after two other actors independently endorse a compatible agenda. Further members join by their own actions after an invitation/observed affiliation. No membership can be silently imposed. Factions are currently **interest coalitions** only, not full legal/institutional units with budgets, enforcement, territorial claims or succession.
- Historical squads, partner ties and voluntary factions are independent overlapping affiliation dimensions. A partnership can link Founders in different squads and factions.

## World and UI limitations

For social testing, locations are an **illustrative four-node local graph**: House, Riverbank, Fields and Ridge. The real Sea map and gate are preserved as design sources, not claimed to be in the runnable engine. The social Observatory is a schematic squad-centered graph, not physical map coordinates.

The current `knowledge_architecture` still has fast saturation from additive fixed learning increments; partial understanding, prerequisites, forgetting and empirically calibrated learning rates remain a future update. Because all 100 Founders initially share the House, information becomes widely accessible even without teaching. Need physical distance, attention budgeting, scarcity and realistic knowledge retrieval before considering simulated diffusion a prediction.

## Crucial integration blockers

1. Main ecological engine still seeds two Founder placeholders rather than 100 social Founders; integration must replace/placeholders, not duplicate identities.
2. `SocialSimulation` and `core.engine.Simulation` instantiate separate books and clocks. A master release must share **one** `Book` and one transaction/event clock, with migration and no duplicate balances.
3. Soul States and ritual/spiritual contract prerequisites must not be inferred from ordinary cognitive skills. Social learning may provide evidence but cannot bypass activation contracts or required physical energy.
4. Full faction governance, political conflict, promises of material delivery, trust calibration, independent belief validation and institution-level collective memory remain unimplemented.
5. Historical officer names and squads are not accurately mapped to all 100 identities; the original roster must be transcribed/verified before release lore assignment.
6. No full physical Sea coordinates, object ownership, real-world geographic navigation or energy-to-matter transformation is implemented.

## Validation / release status

- 85/85 tests passed in `tests/` (72 inherited + 13 new); 15/15 additional ecology and continuity tests pass independently.
- SOCIAL-021 trial: 25 seeds (400–424), 6 arms, 30 decision cycles per run, 100 Founders per run; all 150 runs passed `Book.audit()`.
- Tests establish **internal execution and design-mechanism effects only**. They do not establish realism of human trust, organization, culture, awareness or consciousness.

## Reproducibility

```sh
python -m unittest discover -s tests -q
python -m unittest -q test_soul_ecology test_continuity_loop
python run_social_agents.py --seeds 25 --ticks 30 --workers 4 --out results/social_agents_25
python build_social_dashboard.py --json results/social_agents_25/demo_observatory.json --output results/social_agents_25/social_observatory.html
```
