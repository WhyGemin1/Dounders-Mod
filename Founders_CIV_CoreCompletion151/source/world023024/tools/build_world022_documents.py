"""Generate two source-traceable Word documents for WORLD-022."""
from __future__ import annotations
import json,datetime
from pathlib import Path
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs'
STRESS=json.loads((ROOT/'results/world_stress/summary.json').read_text())
DARK=RGBColor(23,52,59);TEAL=RGBColor(36,103,103);GOLD=RGBColor(178,143,82);GREY=RGBColor(85,105,111)

def cell_shading(cell,fill):
 tcPr=cell._tc.get_or_add_tcPr();shd=OxmlElement('w:shd');shd.set(qn('w:fill'),fill);tcPr.append(shd)
def set_cell_margin(cell,top=105,start=115,bottom=105,end=115):
 tc=cell._tc;tcPr=tc.get_or_add_tcPr();mar=OxmlElement('w:tcMar')
 for tag,val in [('top',top),('start',start),('bottom',bottom),('end',end)]:
  elem=OxmlElement(f'w:{tag}');elem.set(qn('w:w'),str(val));elem.set(qn('w:type'),'dxa');mar.append(elem)
 tcPr.append(mar)
def new_doc(title,kicker,subtitle):
 d=Document();sec=d.sections[0];sec.top_margin=Inches(.79);sec.bottom_margin=Inches(.72);sec.left_margin=Inches(.84);sec.right_margin=Inches(.84)
 style=d.styles['Normal'];style.font.name='Aptos';style.font.size=Pt(9);style.font.color.rgb=DARK
 style.paragraph_format.space_after=Pt(6);style.paragraph_format.line_spacing=1.15
 for name,size,color in [('Title',27,DARK),('Heading 1',15,TEAL),('Heading 2',11.5,DARK),('Heading 3',10.5,TEAL)]:
  s=d.styles[name];s.font.name='Aptos Display' if name=='Title' else 'Aptos';s.font.size=Pt(size);s.font.bold=(name!='Title');s.font.color.rgb=color;s.paragraph_format.space_before=Pt(12 if name!='Title' else 0);s.paragraph_format.space_after=Pt(5)
 header=sec.header.paragraphs[0];header.text='FOUNDERS-CIV  /  WORLD-022   |   EXPERIMENTAL RESEARCH RELEASE';header.style='Caption';header.runs[0].font.color.rgb=GREY
 foot=sec.footer.paragraphs[0];foot.text='Simulation Project  •  7 November 2026  •  Provisional model, not empirical validation';foot.alignment=WD_ALIGN_PARAGRAPH.CENTER;foot.style='Caption'
 p=d.add_paragraph();r=p.add_run(kicker.upper());r.font.color.rgb=GOLD;r.font.bold=True;r.font.size=Pt(10)
 d.add_heading(title,0)
 p=d.add_paragraph(subtitle);p.style='Subtitle';p.runs[0].font.color.rgb=GREY
 d.add_paragraph('Prepared from the uploaded SOCIAL-021 archive and “Note Oct 11, 2026 2.pdf”, with reproducible WORLD-022 tests.').italic=True
 return d

def h(d,s,level=1):d.add_heading(s,level)
def p(d,s='',boldlead=None):
 q=d.add_paragraph()
 if boldlead:q.add_run(boldlead).bold=True
 q.add_run(s)
 return q

def bullets(d,xs):
 for x in xs:d.add_paragraph(x,style='List Bullet')

def table(d,heads,rows,widths=None):
 t=d.add_table(rows=1,cols=len(heads));t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.style='Table Grid'
 for i,hd in enumerate(heads):
  c=t.rows[0].cells[i];c.text=str(hd);cell_shading(c,'23464D')
  for run in c.paragraphs[0].runs:run.font.bold=True;run.font.color.rgb=RGBColor(255,255,255);run.font.size=Pt(8)
  set_cell_margin(c)
 for row in rows:
  cells=t.add_row().cells
  for i,v in enumerate(row):
   cells[i].text=str(v);cells[i].vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER;set_cell_margin(cells[i])
   for para in cells[i].paragraphs:
    para.paragraph_format.space_after=Pt(0)
    for run in para.runs:run.font.size=Pt(7.7)
  if len(t.rows)%2==0:
   for c in cells:cell_shading(c,'EDF4F2')
 d.add_paragraph('')
 return t

def strong(d,head,text):
 q=d.add_paragraph(style='Normal');r=q.add_run(head+'  ');r.bold=True;r.font.color.rgb=TEAL;q.add_run(text)

def make_changes():
 d=new_doc('Founder–World Integration','Implementation and validation report','SOCIAL-021 + ecological core + seed-blueprint construction | WORLD-022 candidate')
 h(d,'Release determination')
 p(d,'WORLD-022 is an experimental, runnable integrated application, not a fully validated civilization simulator. The integration uses the latest supplied SOCIAL-021 package, which itself contains the legacy v0.18 physical core and the later v0.20/021 Founder, Soul, ecology, and social prototypes. The original core files are retained.')
 strong(d,'Central change.','The ecological Simulation and 100-Founder social scheduler now share a single core.ledger.Book and a synchronized clock. Physical changes originate in ledger transactions; social ideas never mint material or energy.')
 h(d,'Implementation at a glance')
 table(d,['Module','Implemented change','Status'],[
  ('world_integration.py','IntegratedWorld executes ecological step → 100 Founder decisions → creation maintenance; shares one Book.','New, tested'),
  ('social_agents.py','Optional external Book wiring while preserving standalone SOCIAL-021 mode.','Backward-compatible, tested'),
  ('SeedRegistry','Draft → researched across two distinct cycles → independent review → validated → planted.','New, tested'),
  ('ConstructRegistry adapter','Funded material transformation for realm/world/underworld/species/dimension with energy reserve and upkeep.','New adapter over existing physics'),
  ('launch_founder_world.py','Localhost-only server, world-state API, cycles, research, review, plant, tend, travel, reset, export.','API smoke-tested'),
  ('founder_world.html','Interactive Sea SVG, House, river, Gate, island-tree-flower creations, 100 Founder inspector, blueprint laboratory.','Browser-rendered prototype')
 ])
 h(d,'Seed ontology and prerequisites')
 p(d,'The symbolic display follows the requested correspondence: realm = island, world = tree, underworld = flower. Species are displayed as sprouts and dimensions as portals. A geographic realm is not a Soul Network Realm. Names, positions, and rules are authored data, not procedurally generated entire environments.')
 table(d,['Seed','Must be planted on','Initial material','Function currently modeled'],[
  ('Realm / island','The Sea','2.50 mass units','Parent spatial construct; physical upkeep and collapse.'),
  ('World / tree','A stable planted realm','1.10 mass units','Child construct; depends on parent stability.'),
  ('Underworld / flower','A stable planted world','0.50 mass units','Dependent energy-maintained construct; underworld recycling not yet simulated.'),
  ('Species / sprout','A stable planted world','0.28 mass units','Designated construct, not yet a reproducing animal population.'),
  ('Dimension / portal','A stable planted realm','0.75 mass units','Dimension-like construct with upkeep and binding.')
 ])
 strong(d,'No instant creation.','An external blueprint can exist without a physical creation. Drafting costs Founder energy; research must occur in two different simulated cycles; a distinct colocated Founder must review the rules. Planting checks owner, parent existence, physical substrate, funded work, and energy reserve before material is transformed.')
 strong(d,'No energy-to-matter alchemy.','The current Book conserves abstract material separately from energy. Planting transfers existing soil substrate into a physical construct using funded work and a transformation toll; it does not convert energy into new mass. This is a deliberate temporary model, not a completed cosmological energy-to-matter rule.')
 h(d,'What a Founder can do now')
 bullets(d,[
 'Autonomously choose study, teach, practice, assist, coordinate, establish voluntary factions, and pursue changing goals, based on SOCIAL-021 policy.',
 'Draft, research, request review of, and plant a seed using an ambition- and goal-sensitive decision candidate; maintain an existing creation using its own available energy.',
 'Cultivate a patch in the physical ecological engine by paying work energy and transforming actual substrate when environmental availability gates permit.',
 'Lose unsaved personal development on death while external planted creations, archives, social relationships, and other actors’ knowledge remain outside the personal checkpoint rollback.',
 'Use the world interface to select one of 100 Founders, revise a goal, move between adjacent House-sector locations, inspect blueprints and creations, or advance the autonomous simulation.'
 ])
 h(d,'Event, state, and causal integrity')
 p(d,'core.engine.Simulation remains physically authoritative for ecology. FounderRegistry tracks 100 true Founder agents; the two old ecological Founder placeholders are deactivated as decision makers, not duplicated as real additional Founders. Founder events and ecology events retain distinct source IDs but can be inspected on a merged cycle-stamped timeline. Ledger transaction IDs provide a physical causality join point; cross-system multi-step actions are not yet a single ACID transaction.')
 p(d,'World rules currently influence construction energy and upkeep and can gate unstable designs. Daylight, moisture, biodiversity, recycling, and lifespan values are recorded for later simulation; they do not yet generate full individual world climates, ecological reproduction, or underworld soul circulation.')
 h(d,'Validation results (re-executed)')
 table(d,['Verification','Observed result','Scope'],[
  ('Original suite','85 / 85 passing','Inherited core, ecology, cognition, SOCIAL-021 checks.'),
  ('Integration + ecology/continuity','24 / 24 passing','9 new WORLD-022 tests + 15 additional inherited targeted tests.'),
  ('Distinct stress interventions','96 / 96 passing','12 stress families with 8 distinct cases each.'),
  ('Aggregate coupled cycles',str(STRESS['total_engine_cycles']),'Across stress scenarios, excluding unit suite.'),
  ('Ledger transactions',f"{STRESS['total_physical_transactions']:,}",'Across stress scenarios.'),
  ('Max absolute mass residual',f"{STRESS['max_abs_mass_error']:.3g}",'Synthetic material units.'),
  ('Max absolute energy residual',f"{STRESS['max_abs_energy_error']:.3g}",'Synthetic energy units.')
 ])
 h(d,'Stress families and interpretation')
 table(d,['Family (8 variants each)','Stress applied','Status'],[
  ('Coupled clock','1–8 full ecological/social cycles; authoritative identity and ledger','Pass'),
  ('Energy shocks','8 graded Founder-energy disruptions','Pass'),
  ('Substrate shocks','8 material reallocations between ecological patches','Pass'),
  ('Malformed seeds','8 invalid kinds, names, coordinates, and rule values','Correct rejection'),
  ('Hierarchy prerequisites','8 missing parent, early plant, self-review, or duplicate research cases','Correct rejection'),
  ('Valid planting','8 rule variants with physical debit and recorded transaction','Pass'),
  ('Maintenance lapse','8 staged maintenance interventions and decay','Pass'),
  ('Checkpoint rollback','8 unsaved skill and memory-loss cases','Pass'),
  ('Social ablations','8 partnered, isolated, no-teach, no-faction, neutral-trust conditions','Pass'),
  ('Deterministic replay','8 identical-seed paired history comparisons','Pass'),
  ('Parent collapse','8 world-tree and underworld-flower cascade interventions','Pass'),
  ('Cognition perturbation','8 targeted trust and goal changes within the world loop','Pass')
 ])
 p(d,'An expected rejection is counted as a passed stressor when rejection is the specified invariant. This is not equivalent to 96 externally validated scientific experiments, and the 96 cases do not establish long-term stability or calibrated psychology.')
 h(d,'How to launch and reproduce')
 bullets(d,[
 'Windows: extract the full ZIP, run START_FOUNDER_WORLD.bat and open http://127.0.0.1:8765/.',
 'macOS/Linux: python3 launch_founder_world.py --port 8765 --seed 400; then visit the same address.',
 'Original regression: python -m unittest discover -s tests -q',
 'Additional integration/continuity: python -m unittest -q test_world_integration test_soul_ecology test_continuity_loop',
 '96 stress interventions: python run_world_stress.py --out results/world_stress',
 'Stress results: results/world_stress/stressors.csv and summary.json; state export: interface button.'
 ])
 h(d,'Known limits and priority work')
 bullets(d,[
 'The Sea SVG positions are illustrative, not physical spatial coordinates in core.engine. The House-sector graph still governs Founder proximity and movement.',
 'Newly planted world trees are funded, persistent constructs, not independently evolved ecological worlds. Realm-islands have no emergent habitats, weather, ownership disputes, or migration between realms.',
 'Species seeds do not yet spawn reproductively viable populations; Underworld flowers do not yet process corpses, soul transfers, or the ten-layer Underworld ledger.',
 'Soul Network coordination remains separate and incomplete; ordinary study must not automatically grant magic capabilities.',
 'The original demographic extinction problem persists in the separate evolution prototype; 96 stress passes must not be interpreted as ecological sustainability.',
 'Creation research learning rates, review thresholds, energy costs, and the work material type are experimental, not accepted canonical values.',
 'Version 0.22 should add a shared episodic event store, partial understanding and forgetting, material classes and energy conversion rules, true spatial pathfinding, institution-maintained projects, and competing world ecology models.'
 ])
 h(d,'Release status')
 p(d,'Recommended label: WORLD-022, an experimental Founder–World integration candidate. Preserve the v0.18 ledger as physical authority. Keep SOCIAL-021 standalone mode supported for comparison and KTC-019 as a dependent cognitive subsystem. Promote to master only after cross-module migration tests and extended ecosystem validation.')
 out=OUT/'WORLD_022_Implementation_and_Stress_Test_Report.docx';d.save(out);return out

def make_notes():
 d=new_doc('Potential Adjustments from the Founder Notes','Source-based design catalog','Notes Oct 11, 2026 · proposals for later releases; not all ideas are accepted canon')
 h(d,'How to read this document')
 p(d,'Each recommendation distinguishes (1) what the October 11 source actually sketches, (2) a possible simulation implementation, and (3) whether WORLD-022 already models it. A handwritten page is a design source, not proof that a proposed mechanic is executable or scientifically validated. The newer requirement that worlds are trees, realms islands, underworlds flowers, and seeds are blueprints comes from the current request, not necessarily from the original note.')
 h(d,'1. Founder organization, identity and social agency')
 table(d,['Source','Potential adjustment','Proposed test / readiness'],[
  ('pp. 18–22','Transcribe and verify the handwritten 100-name roster, founder titles and affiliations; protect canonical names from procedural reassignment.','Roster reconciliation and stable-ID round-trip; NOT yet mapped.'),
  ('p. 19','Replace generic provisional squad labels with the documented eight squads of twelve and four officer assignments where legible.','Squad membership invariants; group assignments remain provisional.'),
  ('pp. 19–22','Model the Founders’ partnership history, disagreements around sovereign authority, and distinct leadership/creation portfolios as memories and goals, not fixed behavior scripts.','Longitudinal coalition and betrayal interventions; partially modeled socially.'),
  ('pp. 20–22','Turn titles such as research, art, war, medicine, beasts, death and creation into initial expertise and commitments without preventing skill development.','Cross-specialty learning and ambition interventions; partially present.'),
  ('pp. 25–27','Use Actions, Memory, Thoughts/Ideas, Attitudes, Goals, Capabilities to explain individual identity; keep subjective interpretation distinct from objective world state.','Ablation and identity continuity tests; SOCIAL-021 + KTC partial.'),
  ('p. 27','Give institutions collective practices, external archives, overlapping memberships, commitments and formal coordination—without attributing a literal individual mind to an organization.','Institution vs individual memory perturbation; not yet integrated.')
 ])
 h(d,'2. The creative powers and seed lifecycle')
 p(d,'Page 23 explicitly lists Founder actions involving energy manipulation, making creations, worlds, dimensions, realms, underworlds and tools. Those are the source-supported powers. The seed-blueprint process and visual symbols below are the current newly requested implementation, not a verbatim page-23 mechanic.')
 table(d,['Concept','Proposed refinement','CURRENT status'],[
  ('Realm / island','Seed defines boundary, anchoring, allowed world slots, transport, construction and maintenance.','Physical island construct and symbolic map icon only.'),
  ('World / tree','Seed defines climate, materials, daylight, water, species access, biological cycles, growth and decline.','Child tree construct; no full simulated climate.'),
  ('Underworld / flower','Seed defines death pathways, material and soul routing, energy recirculation, social access, and compatibility with the ten-layer Underworld.','Dependent flower construct; no dead/soul processing.'),
  ('Species / sprout','Seed specifies body plan, diet, reproduction, maturation, cognition limits, movement, and ecological dependencies.','Physical creation marker; individual generated species not yet present.'),
  ('Dimension / portal','Seed defines capacity, stability, ingress/egress, upkeep, collapse consequences, and local physics exceptions only with explicit rules.','Energy-maintained construct and symbolic portal.'),
  ('Tools and arts','Differentiate a knowledge blueprint, physical artifact, enchantment, Soul ability, and engineering tool; all require separate feasibility checks.','Not yet integrated into seed taxonomy.'),
  ('The seed itself','Track provenance, revision history, reviewed assumptions, prerequisite knowledge, costs, and optional co-authors.','Two-cycle research and one independent review; only one author.')
 ])
 h(d,'3. Space, movement and world interface')
 table(d,['Source','Design proposal','Gap'],[
  ('p. 26','Digitize the Sea map: House, mountain/waterfall, river, cultivation fields, Gate, and named island. Use terrain regions and controllable routes.','WORLD-022 displays landmarks but uses a symbolic four-site proximity graph.'),
  ('pp. 1–3, 9–17','Represent cosmological layers as a hierarchy of connected world/underworld/realm spaces; separate map topology from metaphysical lore.','Universe layers remain design-only.'),
  ('pp. 1–3','Allow maps to change with world-creating actions, artificial barriers, flooding, construction, migration and realm formation.','Canvas adds planted symbolic creations; no evolving terrain grid.'),
  ('pp. 14–17','Disambiguate the Soul Network’s Kingdom/Nation/Realm hierarchy from geographical worlds and connected realms.','Code uses distinct namespaces; UI needs two hierarchy inspectors.'),
  ('p. 26','Expose travel-time, line of sight, access restrictions, river recharge proximity, and physical distances for social encounters.','Travel is one graph edge; no fine physical distances.')
 ])
 h(d,'4. Ecological and energy-function adjustments')
 p(d,'The ecology discussion on pages 24–25 introduces pollinators, parasites, plants, herbivores, predators, scavengers and decomposers and proposes energy/matter flows. It is a useful functional design but its coefficients and sustainability claims need empirical or physically defensible calibration.')
 table(d,['Proposed subsystem','Source / mechanism','Validation requirement'],[
  ('Pollination','pp. 24–25; mutualist services influence plant reproduction.','Ablate pollinators and measure seed set, biodiversity, and producer recovery.'),
  ('Parasites','pp. 24–25; host energy drain and reduced fitness.','Independent host-health and population trajectory checks.'),
  ('Decomposition','pp. 24–25; dung and carcasses recycle nutrients.','Conserve mass by material classes; demonstrate nutrient limitation.'),
  ('Trophic balance','pp. 24–25; producer→consumer→decomposer loops.','Multiple-generation persistence, food-web stability under shocks.'),
  ('Energy flow','pp. 23–25; river/House energy and transformed matter.','Define exact boundary conditions and work ledger; avoid creating mass from energy without conversion rules.'),
  ('Creations as habitats','p. 23 and p. 26; spatial habitats for mortal creations.','Make generated worlds host real actors before asserting autonomous civilization.'),
  ('Resource distribution','p. 26; fields, river and Gate locations.','Couple resources to actual travel paths and territorial decisions.')
 ])
 h(d,'5. Governance, institutions and technological systems')
 table(d,['Notes region','Possible adjustment','Scientific/engineering caution'],[
  ('pp. 5–7','Different histories, species purposes and governance structures can produce competing institutional models across worlds.','Keep fictional lore separate from empirically claimed social laws.'),
  ('pp. 7–8, 28–29','Economy, military power, religion, culture, law, status and central power can be distinct institutional dimensions shaping cooperation and conflict.','Make budgets, members, rules, enforcement, legitimacy and outcomes observable.'),
  ('pp. 28–29','Collective cognition through organized thought, religion and scientific inquiry can be represented as organizations producing knowledge and norms.','An institution is not a person; model distributed records and individual beliefs.'),
  ('pp. 30–33','Digital Information Software / externalized cognition suggests archives, computers, communications and institutional knowledge as actor-external resources.','Technical availability is not identical to an actor knowing or understanding information.'),
  ('pp. 30–33','Energy limits on technology could become competing infrastructure policies and resource risks.','The note’s nuclear inevitability, historical timber-crisis, and fusion forecasts are hypotheses or assertions, not verified canon or engineering constraints.')
 ])
 h(d,'6. Suggested implementation priorities')
 table(d,['Priority','Adjustment and model value','Promotion gate'],[
  ('P0','Accurate name/role/squad roster from source; stable identity + continuity.','Manual review of all 100 names; identity serialization tests.'),
  ('P0','Seed prereq graph and persistent provenance, partial knowledge, forgetting and skill practice.','Calibrated learning curves; failing prerequisites block actual planting.'),
  ('P0','Founder-created islands/trees/flowers as nested geographic objects with real position and boundaries.','Reachability, occupancy, collision, topological integrity tests.'),
  ('P1','Distributed ownership and coordinated research councils; shared project reserves.','Voluntary consent, withdrawal, budget and ledger trace tests.'),
  ('P1','Death/Underworld/cycle mechanics that link living actors and dead material.','One-cycle mass/energy audit; cross-world migration rules.'),
  ('P1','Generated world ecological biomes, species and reproducing populations.','100+ temporal-step population persistence with seasonal resources.'),
  ('P1','Political disputes and faction legitimacy, rules, enforcement and succession.','Matched controls and institution capture/dissolution stressors.'),
  ('P2','Technology and external knowledge infrastructures, including archives/computers.','Reliability and outage shock tests with source provenance.'),
  ('P2','Soul Network evidence-based States across contexts; avoid automatic unlock.','Ablations practice, semantics, cross-context transfer and vow validation.')
 ])
 h(d,'7. Canon and research integrity policy')
 bullets(d,[
 'Keep three flags for each rule: source-supported worldbuilding canon, simulated implementation state, and empirical evidence status.',
 'The original note supplies themes, functions, maps and lore; it does not specify all thresholds, material-conversion laws, optimal algorithms or accurate simulation coefficients.',
 'Do not count a numerical simulator producing its own programmed effect as evidence of real cognition, trust, consciousness, or ecological sustainability.',
 'Never let a blueprint create material or bypass the existing House/river energy ledger by declaration.',
 'When adding autonomous institution governance, preserve voluntary membership and Founder individuality rather than prescripting political outcomes.'
 ])
 out=OUT/'WORLD_022_Notes_Based_Potential_Adjustments.docx';d.save(out);return out

if __name__=='__main__':
 print(make_changes());print(make_notes())
