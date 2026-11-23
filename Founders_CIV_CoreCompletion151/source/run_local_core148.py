#!/usr/bin/env python3
"""Local, configurable long-horizon runner for actual Cycle147 Core Completion engine.

Keeps exactly 100 canonical Founders, one World Tree Book and two schedulers.
Only initial *bridge* animal cohorts are configurable: native resident spawning
remains part of WORLD-023/024 and is not replaced by fake agents.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import json
import os
from pathlib import Path
import pickle
import sys
import time

from ecoregulation_148 import UnifiedEcoRegulation148
from habitat_bridge import SPECIES
from trophic_guilds_cycle138 import GUILD_FOUNDERS
from species_life_02115 import PROFILES

CORE_MINIMUM = 8  # four male/female pairs per original species; source invariant
BASE_CORE = {key: CORE_MINIMUM for key in SPECIES}
GUILD_DEFAULT = dict(GUILD_FOUNDERS)
ALL_SPECIES = tuple(BASE_CORE) + tuple(GUILD_DEFAULT)
DEFAULT_TOTAL = sum(BASE_CORE.values()) + sum(GUILD_DEFAULT.values())


def distribute_animals(total: int) -> dict[str, int]:
    """Honor Core145's mandatory original five founding families and distribute extras."""
    minimum = sum(BASE_CORE.values())
    if total < minimum:
        raise ValueError(f'Core145 requires >= {minimum} bridge animals: four founding pairs for each of five core species.')
    if total > 10000:
        raise ValueError('Initial bridge actor count above 10,000 is not supported by this research runner.')
    extra = total - minimum
    weights = GUILD_DEFAULT
    denominator = sum(weights.values())
    quotas = {s: extra * n / denominator for s, n in weights.items()}
    allocated = {s: int(quotas[s]) for s in weights}
    remainder = extra - sum(allocated.values())
    ranked = sorted(weights, key=lambda s: (-(quotas[s] - allocated[s]), ALL_SPECIES.index(s)))
    for s in ranked[:remainder]:
        allocated[s] += 1
    return {**BASE_CORE, **allocated}


def custom_counts(assignments: list[str]) -> dict[str, int]:
    counts = {**BASE_CORE, **GUILD_DEFAULT}
    seen = set()
    for item in assignments:
        if '=' not in item:
            raise ValueError(f'Expected SPECIES=NUMBER, got {item!r}')
        name, quantity = item.split('=', 1)
        name = name.strip().lower().replace('-', '_')
        if name not in ALL_SPECIES:
            raise ValueError(f'Unknown species {name!r}; use --list-species')
        if name in seen:
            raise ValueError(f'Duplicate --species for {name}')
        seen.add(name)
        try:
            number = int(quantity)
        except ValueError as e:
            raise ValueError(f'Invalid count for {name}: {quantity!r}') from e
        if name in BASE_CORE and (number < 8 or number % 2):
            raise ValueError(f'{name}: this engine requires >=8 and an even number (founding pairs).')
        if number < 0 or number > 10000:
            raise ValueError(f'{name}: count must be in range 0..10000')
        counts[name] = number
    return counts


def make_parser():
    parser = argparse.ArgumentParser(
        description='Cycle147 actual integrated simulation: configure bridge animals, run, checkpoint, resume.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('--interactive', action='store_true', help='Ask for basic options interactively.')
    parser.add_argument('--list-species', action='store_true', help='Print current 13 species and minimums, then exit.')
    parser.add_argument('--seed', type=int, default=100001, help='Deterministic seed (Python hash seed fixed by launch script).')
    parser.add_argument('--days', type=int, default=360, help='Additional world days to run, including after --resume.')
    parser.add_argument('--animals', type=int, default=None,
                        help=f'EXACT total initial bridge animals; must be >=40. Omit for original {DEFAULT_TOTAL}.')
    parser.add_argument('--species', action='append', default=[], metavar='NAME=COUNT',
                        help='Override one species count; repeat for others. Not combinable with --animals.')
    parser.add_argument('--grid-size', type=int, default=8, help='Spatial microcell width, range 2..64.')
    parser.add_argument('--governance', choices=('collective', 'owner', 'fragmented', 'none'), default='collective')
    parser.add_argument('--output', default=None, help='Directory for CSV, metadata and checkpoints (defaults to results/core148_run or checkpoint folder on resume).')
    parser.add_argument('--report-every', type=int, default=30, help='Days between CSV observations.')
    parser.add_argument('--checkpoint-every', type=int, default=90, help='Days between saved resumable checkpoints; 0 for end-only.')
    parser.add_argument('--maintenance-factor', type=float, default=1.0, help='EXPERIMENT ONLY: 1.0 is unmodified physiology; 0.75 reduces demand for a matched contrast.')
    parser.add_argument('--disable-predation', action='store_true', help='EXPERIMENT ONLY: disable hunting to test prey-demographic sensitivity; predators still need food.')
    parser.add_argument('--disable-local-tracking', action='store_true', help='Matched control: disable Cycle148 local, physically paid prey tracking.')
    parser.add_argument('--disable-mate-search', action='store_true', help='Matched control: disable Cycle148 adjacent-habitat mate seeking.')
    parser.add_argument('--disable-fuel-flex', action='store_true', help='Run unchanged Core146 physiology as the matched control.')
    parser.add_argument('--disable-trophic-diet', action='store_true', help='Core145 control: turn off new carnivore and plant-eater diet physiology.')
    parser.add_argument('--disable-trophic-hunting', action='store_true', help='Core145 control: turn off new density/refuge/satiation hunting rules and fair event order.')
    parser.add_argument('--disable-trophic-provisioning', action='store_true', help='Core145 control: turn off new canid parent food sharing.')
    parser.add_argument('--resume', metavar='CHECKPOINT.pkl', help='Continue a prior run. Initial counts and seed are loaded from checkpoint.')
    parser.add_argument('--quiet', action='store_true', help='Suppress per-observation console lines.')
    parser.add_argument('--stop-on-world-collapse', action='store_true',
                        help='Stop and save immediately if the World Tree becomes archived/collapsed.')
    return parser


def prompt_options(args):
    print('\nFounders–CIV Core148 — long-run setup')
    print('Canon requires 100 Founders; the adjustable population is the 13 bridge animal species.')
    print('The native World Tree residents remain managed by their own scheduler.')
    for field, label, default in (
        ('seed', 'Random seed', args.seed),
        ('days', 'World days to run (360, 720, 1080...)', args.days),
        ('animals', f'Initial bridge animals (minimum 40; archive default {DEFAULT_TOTAL})', DEFAULT_TOTAL),
        ('report_every', 'Report every N days', args.report_every),
        ('checkpoint_every', 'Checkpoint every N days', args.checkpoint_every),
    ):
        answer = input(f'{label} [{default}]: ').strip()
        setattr(args, field, int(answer) if answer else default)
    dest = input(f'Output folder [{args.output or "results/core148_run"}]: ').strip()
    if dest:
        args.output = dest
    return args


def validate_args(args):
    if not .25 <= args.maintenance_factor <= 2.:
        raise ValueError('--maintenance-factor must be in 0.25..2.0')
    if args.resume and (args.maintenance_factor!=1. or args.disable_predation):
        raise ValueError('Resume uses treatment stored in checkpoint; do not change experiment flags.')
    if args.days < 0:
        raise ValueError('--days must be >=0')
    if args.report_every < 1:
        raise ValueError('--report-every must be >=1')
    if args.checkpoint_every < 0:
        raise ValueError('--checkpoint-every must be >=0')
    if not 2 <= args.grid_size <= 64:
        raise ValueError('--grid-size must be 2..64')
    if args.animals is not None and args.species:
        raise ValueError('Use either --animals or repeated --species, not both.')
    if args.resume and (args.animals is not None or args.species):
        raise ValueError('Cannot change initial species populations while resuming a checkpoint.')
    if args.resume and args.interactive:
        raise ValueError('Use --resume without --interactive.')


def first_checkpoint(sim):
    b = sim.host.book
    if not (sim.host.book is sim.bridge.book is sim.bridge.tree.book):
        raise AssertionError('Critical: Book not shared by host, bridge and tree')
    if len(sim.host.sim.founders.people) != 100:
        raise AssertionError('Canonical Founder count mismatch')
    audit = b.audit()
    if audit['rejections'] != 0:
        raise AssertionError(f'Book rejections detected: {audit}')
    return audit


def save_checkpoint(sim, target: Path):
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix('.partial')
    with tmp.open('wb') as f:
        pickle.dump(sim, f, protocol=pickle.HIGHEST_PROTOCOL)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, target)


def snapshot(sim, elapsed_seconds, initial_counts):
    b = sim.host.book
    tree = sim.bridge.tree
    a = [x for x in sim.bridge.actors.values() if x.alive]
    counts = Counter(x.species for x in a)
    g1 = [x for x in sim.bridge.actors.values() if x.generation == 1]
    g2 = [x for x in sim.bridge.actors.values() if x.generation >= 2]
    audit = first_checkpoint(sim)
    row = dict(seed=sim.seed, day=sim.days, founders_total=len(sim.host.sim.founders.people),
        founders_alive=sum(x.alive for x in sim.host.sim.founders.people.values()),
        bridge_living=len(a), bridge_ever_created=len(sim.bridge.actors),
        native_living=tree.population, world_state=tree.state,
        g1_births=len(g1), g1_living=sum(x.alive for x in g1),
        g1_ever_mature=sum(x.age >= PROFILES[x.species].maturity for x in g1),
        g2_births=sum(x.generation==2 for x in sim.bridge.actors.values()),
        g2_living=sum(x.alive and x.generation==2 for x in sim.bridge.actors.values()),
        g2plus_births=len(g2), g2plus_living=sum(x.alive for x in g2),
        g2_births_exact=sum(x.generation==2 for x in sim.bridge.actors.values()),
        g3_births_exact=sum(x.generation==3 for x in sim.bridge.actors.values()),
        g4plus_births=sum(x.generation>=4 for x in sim.bridge.actors.values()),
        native_births=tree.counters.get('tree_birth', 0),
        native_gut_meals=tree.counters.get('native_gut_meals', 0),
        bridge_gut_meals=sim.bridge.physiology_metrics.get('fee_free_ingestion', 0),
        book_rejections=audit['rejections'],
        mass_residual=audit['mass_error'], energy_residual=audit['energy_error'],
        book_transactions=audit['transactions'], elapsed_wall_seconds=round(elapsed_seconds, 3))
    for sp in ALL_SPECIES:
        row['g2_births__' + sp] = sum(x.generation==2 and x.species==sp for x in sim.bridge.actors.values())
        row['alive__' + sp] = counts[sp]
        row['initial__' + sp] = initial_counts.get(sp, '')
    return row


def read_metadata(target):
    if target.exists():
        return json.loads(target.read_text())
    return None


def run(args):
    validate_args(args)
    out = Path(args.output or (Path(args.resume).expanduser().parent if args.resume else 'results/core148_run')).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    timeline_file = out / 'timeline.csv'
    metadata_file = out / 'run_metadata.json'
    checkpoint_file = out / 'latest_checkpoint.pkl'
    started = time.monotonic()
    if args.resume:
        cp_path = Path(args.resume).expanduser().resolve()
        # Checkpoints are Python pickle: never load untrusted downloaded pickles.
        with cp_path.open('rb') as f:
            sim = pickle.load(f)
        if not isinstance(sim, UnifiedEcoRegulation148):
            raise TypeError('Checkpoint does not contain a Cycle147 Core Completion simulation.')
        first_checkpoint(sim)
        metadata = read_metadata(metadata_file)
        if metadata and metadata.get('engine') != 'UnifiedEcoRegulation148':
            raise ValueError('Output folder contains incompatible engine metadata.')
        counts = (metadata or {}).get('initial_bridge_counts') or {sp:None for sp in ALL_SPECIES}
        if timeline_file.exists():
            with timeline_file.open(newline='') as f:
                found = list(csv.DictReader(f))
            if found and int(found[-1]['day']) > sim.days:
                raise ValueError('Existing timeline is ahead of supplied checkpoint; choose a new --output directory.')
        print(f'Resuming checkpoint at day {sim.days}, seed {sim.seed}', flush=True)
    else:
        counts = (distribute_animals(args.animals) if args.animals is not None
                  else custom_counts(args.species))
        if sum(counts.values()) > 200:
            print('WARNING: >200 starting bridge animals may exceed physical Book resources and run very slowly.', file=sys.stderr)
        core_counts = {s:counts[s] for s in SPECIES}
        guild_counts = {s:counts[s] for s in GUILD_DEFAULT}
        try:
            sim = UnifiedEcoRegulation148(seed=args.seed, governance=args.governance,
                      counts=core_counts, guild_counts=guild_counts, grid_size=args.grid_size,
                      maintenance_factor=args.maintenance_factor, predation=not args.disable_predation,
                      trophic_diet=not args.disable_trophic_diet,
                      trophic_hunting=not args.disable_trophic_hunting,
                      trophic_provisioning=not args.disable_trophic_provisioning,
                      fuel_flex=not args.disable_fuel_flex,
                      local_tracking=not args.disable_local_tracking,
                      mate_search=not args.disable_mate_search)
        except Exception as e:
            raise RuntimeError('Core148 population initialization failed. All animals must be funded '
                'by real World Tree resources; try a lower --animals count or different per-species sizes.') from e
        audit = first_checkpoint(sim)
        current_counts = Counter(x.species for x in sim.bridge.actors.values())
        if any(current_counts[sp] != counts[sp] for sp in ALL_SPECIES):
            raise AssertionError('Engine silently changed requested founding cohort. '
                                 f'Requested {counts}; actual {dict(current_counts)}')
        metadata = dict(schema='founders-civ/local-runner-v1',engine='UnifiedEcoRegulation148',
            source='Founders_CIV_Cycle147_Engine_Experimental.zip',
            seed=args.seed,governance=args.governance,grid_size=args.grid_size,
            maintenance_factor=args.maintenance_factor,predation_enabled=not args.disable_predation,
            trophic_diet_enabled=not args.disable_trophic_diet,
            trophic_hunting_enabled=not args.disable_trophic_hunting,
            trophic_provisioning_enabled=not args.disable_trophic_provisioning,
            fuel_flex_enabled=not args.disable_fuel_flex,
            local_tracking_enabled=not args.disable_local_tracking,
            mate_search_enabled=not args.disable_mate_search,
            initial_bridge_counts=counts,initial_bridge_total=sum(counts.values()),
            canonical_founders=100, native_population_at_start=sim.bridge.tree.population,
            book_initial_audit=audit,
            notes=['Synthetic species parameters are not biologically calibrated.',
                'Bridge animal counts exclude 100 Founders and native World Tree residents.',
                'Engine retains two demographic schedulers and one Book.',
                'Core148 tracking and mate-search are independent experimental treatments.',
                'No G2 or long-run viability is guaranteed.'])
        metadata_file.write_text(json.dumps(metadata, indent=2) + '\n')
        print(f'Initialized: {sum(counts.values())} bridge animals / {len(counts)} species, '
              f'{len(sim.host.sim.founders.people)} Founders, '
              f'{sim.bridge.tree.population} native residents, seed {args.seed}', flush=True)

    end_day = sim.days + args.days
    if not timeline_file.exists():
        with timeline_file.open('w', newline='') as f:
            row = snapshot(sim, 0., counts)
            w = csv.DictWriter(f, fieldnames=list(row))
            w.writeheader()
            w.writerow(row)
        print(f'Day {sim.days}: {sum(x.alive for x in sim.bridge.actors.values())} bridge alive; '
              f'World={sim.bridge.tree.state}', flush=True)
    observed_last = None
    interrupted = False
    collapsed_stop = False
    try:
        while sim.days < end_day:
            sim.step()
            if sim.days % args.report_every == 0 or sim.days == end_day:
                row = snapshot(sim, time.monotonic()-started, counts)
                with timeline_file.open('a', newline='') as f:
                    w=csv.DictWriter(f, fieldnames=list(row))
                    w.writerow(row)
                observed_last = row
                if not args.quiet:
                    print(f"Day {sim.days:>5} | bridge {row['bridge_living']:>4} | native {row['native_living']:>4} | "
                          f"G1 {row['g1_births']:>3}, G2 {row['g2_births']:>3} | "
                          f"World {row['world_state']} | Book reject {row['book_rejections']}", flush=True)
            if args.checkpoint_every and sim.days % args.checkpoint_every == 0:
                save_checkpoint(sim, checkpoint_file)
            if args.stop_on_world_collapse and sim.bridge.tree.state not in ('active', 'germinating'):
                print(f'World state became {sim.bridge.tree.state} at day {sim.days}; saving and stopping.',flush=True)
                collapsed_stop = True
                break
    except KeyboardInterrupt:
        interrupted = True
        print('\nInterrupted: saving resumable checkpoint.', file=sys.stderr)
    finally:
        save_checkpoint(sim, checkpoint_file)
        if observed_last is None or observed_last['day'] != sim.days:
            observed_last = snapshot(sim, time.monotonic()-started, counts)
            with timeline_file.open('a', newline='') as f:
                w = csv.DictWriter(f, fieldnames=list(observed_last))
                w.writerow(observed_last)
        # The trait archive is diagnostic and does not change any actor state or
        # physical Book account. It includes dead actors for lineage analysis.
        traits_file=out/'individual_traits.csv'
        from species_traits_143 import FIELDS
        with traits_file.open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=['actor_id','species','sex','generation',
                'parent','age_days','alive','habitat',*FIELDS])
            writer.writeheader()
            for actor in sorted(sim.bridge.actors.values(),key=lambda x:x.id):
                t=sim.bridge.phenotypes[actor.id]
                writer.writerow(dict(actor_id=actor.id,species=actor.species,
                    sex=actor.sex,generation=actor.generation,parent=actor.parent,
                    age_days=actor.age,alive=actor.alive,habitat=actor.habitat,
                    **t.asdict()))
        physiology_file=out/'physiology_and_world_flows.json'
        physiology=dict(days=sim.days,physiology=sim.bridge.physiology_report(),
            fuel_flex_enabled=sim.bridge.fuel_flex_enabled,
            fuel_flex_metrics=dict(sim.bridge.fuel_flex_metrics),
            ecoregulation_flags=dict(sim.bridge.ecoregulation_flags),
            ecoregulation_metrics=dict(sim.bridge.ecoregulation_metrics),
            trait_metrics=dict(sim.bridge.trait_metrics),
            food_lot_metrics=dict(sim.bridge.lots.metrics),
            world_support=sim.world_support.report() if sim.world_support else None,
            live_species=sim.bridge.five_phase_report()['species'],
            reproductive_blockers=dict(sim.bridge.life_blockers),
            reproductive_mechanisms=dict(sim.bridge.life_metrics),
            predation_enabled=sim.bridge.predation_enabled,
            maintenance_factor=sim.bridge.maintenance_factor)
        physiology_file.write_text(json.dumps(physiology,indent=2,default=str)+'\n')
        summary=dict(engine='UnifiedEcoRegulation148',status='interrupted' if interrupted else ('world_collapsed' if collapsed_stop else 'completed'),
            seed=sim.seed,day_reached=sim.days,expected_end_day=end_day,
            initial_bridge_counts=counts,final=observed_last,
            checkpoint=str(checkpoint_file),timeline=str(timeline_file),
            individual_traits=str(traits_file),physiology_flows=str(physiology_file),
            reminder='G2 is demonstrated in pilots; this does not establish 13-species persistence or empirical calibration')
        (out / 'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
        print('Saved checkpoint:',checkpoint_file, flush=True)
        print('Saved results:',timeline_file, flush=True)
    return 130 if interrupted else 0


def main(argv=None):
    parser=make_parser()
    args=parser.parse_args(argv)
    if args.list_species:
        print(f'Canonical Founders: 100. Default initial bridge animal actors: {DEFAULT_TOTAL}.')
        for sp in ALL_SPECIES:
            n=BASE_CORE.get(sp,GUILD_DEFAULT.get(sp,0))
            rule='(min 8, even)' if sp in BASE_CORE else '(0+ allowed)'
            print(f'  {sp:<22} default={n:<3} {rule}')
        return 0
    if args.interactive:
        args=prompt_options(args)
    try:
        return run(args)
    except (ValueError,TypeError,RuntimeError,AssertionError,OSError) as e:
        print(f'ERROR: {e}',file=sys.stderr)
        if e.__cause__ is not None:
            print(f'CAUSE: {e.__cause__}',file=sys.stderr)
        return 2

if __name__=='__main__':
    raise SystemExit(main())
