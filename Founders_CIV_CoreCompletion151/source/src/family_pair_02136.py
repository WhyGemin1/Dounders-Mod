"""Cycle039 opt-in founding family pairs and shared finite reproductive investment.

Uses the existing WORLD-023 Book and one host clock. Every initial cohort
starts with >=4 adult F/M pairs per species. All family provisioning debits
real habitat biomass/chemical energy and partner metabolic reserve. It does
not guarantee conception, offspring survival, or World Tree persistence.
"""
from collections import Counter
from energy_adaptation_02135 import HabitatBridge238
from species_life_02115 import PROFILES, MASS_SCALE, YEAR
from habitat_bridge import SPECIES

MIN_PAIRS = 4
PARTNER_RESERVE_FLOOR = .010
PARTNER_SHARE_CEILING = .0012
PARENTAL_PROVISION_MASS = .0025
PARENTAL_WORK_COST = .00012
PARENTAL_CHEM_COST_PER_MASS = .075
BONDED_COURTSHIP_COST = .00010
BONDED_CONCEPTION_P = .060  # synthetic alternative to baseline opportunity


class HabitatBridge239(HabitatBridge238):
    def __init__(self, tree, seed=9711, counts=None, *, family_benefits=True, **kwargs):
        self.family_benefits = bool(family_benefits)
        self._founder_pair_initialization = True
        self.family_pairs = {}
        self.partner_of = {}
        self.family_fluxes = Counter()
        if counts is None:
            counts = {s: 2*MIN_PAIRS for s in SPECIES}
        if set(counts) != set(SPECIES):
            raise ValueError('family-start requires an explicit count for all five species')
        if any(type(v) is not int or v < 2*MIN_PAIRS or v % 2 for v in counts.values()):
            raise ValueError('family-start requires >=4 complete pairs per species')
        super().__init__(tree, seed=seed, counts=counts, **kwargs)
        self._founder_pair_initialization = False
        for species in SPECIES:
            original = [a for a in self.actors.values() if a.species == species]
            if len(original) != counts[species]:
                raise RuntimeError('physical source could not fund requested founding pairs')
            for n in range(0, len(original), 2):
                female, male = original[n:n+2]
                # The shared source has alternating sexes per species because each
                # species has an even count, but validate instead of assuming.
                if (female.sex, male.sex) != ('F', 'M'):
                    raise RuntimeError('invalid initial family sex pairing')
                if female.stage != 'adult' or male.stage != 'adult':
                    raise RuntimeError('initial family was not reproductively adult')
                pair_id = f'family:{species}:{n//2+1}'
                self.family_pairs[pair_id] = (female.id, male.id)
                self.partner_of[female.id] = male.id
                self.partner_of[male.id] = female.id
                female.partner_id = male.id
                male.partner_id = female.id
                female.family_id = pair_id
                male.family_id = pair_id
                self._log('founding_pair', family=pair_id, female=female.id,
                          male=male.id, habitat=female.habitat)
        self._check_registry()

    def _initial_age(self, p):
        if getattr(self, '_founder_pair_initialization', False):
            return self.rng.randrange(p.maturity, p.senescence)
        return super()._initial_age(p)

    def partner(self, a):
        other = self.actors.get(self.partner_of.get(a.id))
        if not other or not other.alive or not a.alive:
            return None
        if other.habitat != a.habitat or other.species != a.species:
            return None
        return other

    def _metabolize(self, a):
        # Transferring existing energy is possible before the receiver burns it.
        donor = self.partner(a)
        if self.family_benefits and donor is not None:
            receiver_key = self.physical.reserve(a)
            donor_key = self.physical.reserve(donor)
            missing = max(0., .009-self.book.energy[receiver_key])
            available = max(0.,self.book.energy[donor_key]-PARTNER_RESERVE_FLOOR)
            transfer = min(missing, available, PARTNER_SHARE_CEILING)
            if transfer>1e-12:
                self.book.move(energy=[(donor_key,receiver_key,transfer)])
                self.family_fluxes['partner_support_energy'] += transfer
                self.family_fluxes['partner_support_events'] += 1
                self._log('pair_support',giver=donor.id,receiver=a.id,energy=transfer)
        # Opt-in juvenile demand reduction AFTER the normal family-support transfer.
        # Retains one Book and the original adult metabolic dispatch.
        factor = getattr(self, '_juvenile_metabolic_multiplier', 1.0)
        if factor < 1.0 and a.parent is not None and a.age < PROFILES[a.species].maturity:
            profile = PROFILES[a.species]
            demand = .001 * (.5 + .5 * profile.metabolism / .1) * factor
            reserve = self.physical.reserve(a)
            burn = min(self.book.energy[reserve], demand)
            if burn > 0:
                self.book.move(energy=[(reserve, 'environment:heat', burn)])
            a.condition = min(1., a.condition + .007) if burn >= .8 * demand else max(0., a.condition - .035)
            return None
        return super()._metabolize(a)

    def evaluate_needs(self, a):
        action, hunger, danger = super().evaluate_needs(a)
        # Cycle114 opt-in juvenile foraging: prioritize existing local food,
        # without changing food quantities, predator behavior or Book accounts.
        if (getattr(self, '_juvenile_foraging_priority', False)
            and a.alive and a.parent is not None
            and a.age < PROFILES[a.species].maturity
            and a.species in ('field_mouse', 'meadow_grazer', 'forest_browser')
            and a.stage != 'dependent'
            and self.book.energy[self.physical.reserve(a)] < .028
            and self.book.mass[self.physical.plant(a)] > .04
            and action not in ('flee', 'hide')
            and action != 'feed'):
            self.needs_choices[f'{a.species}:{action}'] -= 1
            self.needs_choices[f'{a.species}:feed'] += 1
            self.needs_last[a.id] = 'feed'
            self._log('juvenile_foraging_priority', actor=a.id, previous=action,
                      habitat=a.habitat)
            action = 'feed'
        return action, hunger, danger

    def _provision_mother(self, mother, father):
        p=PROFILES[mother.species]
        if (mother.stage!='adult' or father.stage!='adult'
            or mother.pregnant_until is not None or mother.condition<.55
            or father.condition<.55):
            return False
        # A father can bring local vegetation to the maternal store. Material
        # cannot appear without a debit to the Tree plant account, and labor
        # must be paid from his own reserves. A second real chem debit funds
        # the maternal embodied food-energy account.
        maternal=self.physical.maternal(mother)
        required=p.birth_cost*MASS_SCALE
        shortage=max(0.,required-self.book.mass[maternal])
        if shortage<=1e-10:return False
        # Predators require real carrion rather than converting vegetation
        # into their offspring. Herbivores access plants; carrion birds use
        # local carcasses when available, otherwise a plant/fruit fallback.
        carrion=self.carrion(mother.habitat)
        use_carrion=(mother.species=='ridge_hound' or
                     (mother.species=='carrion_bird' and self.book.mass[carrion]>=.0004))
        source=carrion if use_carrion else self.tree.acct('plant',mother.habitat)
        energy_source=(self.physical.carrion_energy(mother.habitat) if use_carrion
                       else self.tree.acct('chem',mother.habitat))
        donor=self.physical.reserve(father)
        remaining_floor=0. if use_carrion else .04
        amount=min(shortage,PARENTAL_PROVISION_MASS,
                   max(0.,self.book.mass[source]-remaining_floor))
        needed_energy=amount*PARENTAL_CHEM_COST_PER_MASS
        if (amount<.0004 or self.book.energy[donor]<PARTNER_RESERVE_FLOOR+PARENTAL_WORK_COST
            or self.book.energy[energy_source]<needed_energy+.0001):
            self.family_fluxes['provision_resource_denied']+=1
            return False
        self.physical.convert([(source,maternal,amount)])
        self.book.move(energy=[(donor,'environment:heat',PARENTAL_WORK_COST),
                               (energy_source,self.physical.maternal_energy(mother),needed_energy)])
        self.family_fluxes['maternal_mass_provisioned']+=amount
        self.family_fluxes['maternal_energy_provisioned']+=needed_energy
        self.family_fluxes['paternal_work_energy_paid']+=PARENTAL_WORK_COST
        self.family_fluxes['provision_events']+=1
        self._log('pair_provision',father=father.id,mother=mother.id,
                  food_source='carrion' if use_carrion else 'plant',
                  mass=amount,work_energy=PARENTAL_WORK_COST)
        return True

    def _reproduce(self):
        phase=self.day%YEAR
        for family_id,(mother_id,father_id) in (list(self.family_pairs.items()) if self.family_benefits else []):
            mother=self.actors[mother_id]
            father=self.actors[father_id]
            if (not mother.alive or not father.alive or
                self.partner(mother) is not father):
                continue
            p=PROFILES[mother.species]
            if p.breeding[0]-14<=phase<=p.breeding[1]:
                self._provision_mother(mother,father)
            # Independent mating *opportunity* funded by both parents, not a
            # birth guarantee. Existing gestation, eligibility and maternal mass
            # gates are identical to the parent scheduler.
            if (mother.pregnant_until is not None or mother.stage!='adult'
                or father.stage!='adult' or not(p.breeding[0]<=phase<=p.breeding[1])
                or mother.condition<.65 or father.condition<.65
                or self.book.mass[self.physical.live(mother)]<p.adult_mass()*.70
                or self.day-mother.last_birth_day<p.gestation+p.independence
                or self.book.mass[self.physical.maternal(mother)]<p.birth_cost*MASS_SCALE):
                continue
            mr=self.physical.reserve(mother)
            fr=self.physical.reserve(father)
            if min(self.book.energy[mr],self.book.energy[fr]) < .012+BONDED_COURTSHIP_COST:
                continue
            self.book.move(energy=[(mr,'environment:heat',BONDED_COURTSHIP_COST),
                                   (fr,'environment:heat',BONDED_COURTSHIP_COST)])
            self.family_fluxes['bonded_courtship_attempts']+=1
            self.family_fluxes['courtship_work_energy_paid']+=2*BONDED_COURTSHIP_COST
            if self.rng.random()<BONDED_CONCEPTION_P:
                mother.pregnancy_father=father.id
                mother.pregnant_until=self.day+p.gestation
                self.family_fluxes['bonded_conceptions']+=1
                self._log('conception',mother=mother.id,father=father.id,
                          due=mother.pregnant_until,species=mother.species,
                          reason='funded_bonded_courtship')
        return super()._reproduce()

    def _birth(self,mother):
        old=set(self.actors)
        father=self.actors.get(mother.pregnancy_father)
        children=super()._birth(mother)
        if self.family_benefits and children and father and father.alive and self.partner_of.get(mother.id)==father.id:
            for child_id in set(self.actors)-old:
                child=self.actors[child_id]
                if child.parent==mother.id:
                    child.caregiver_ids.add(father.id)
                    child.family_id=getattr(mother,'family_id',None)
                    self.family_fluxes['two_parent_children']+=1
                    self._log('father_assigned',father=father.id,child=child.id)
        return children

    def _check_registry(self):
        super()._check_registry()
        if hasattr(self,'family_pairs'):
            for fid,(f,m) in self.family_pairs.items():
                assert self.partner_of.get(f)==m and self.partner_of.get(m)==f
                assert self.actors[f].species==self.actors[m].species

    def census(self):
        out=super().census()
        out['family_pairs_initial']=len(self.family_pairs)
        out['family_benefits_enabled']=self.family_benefits
        out['family_pairs_intact']=sum(1 for f,m in self.family_pairs.values()
                       if self.actors[f].alive and self.actors[m].alive)
        out['family_fluxes']={k:round(v,9) for k,v in sorted(self.family_fluxes.items())}
        return out
