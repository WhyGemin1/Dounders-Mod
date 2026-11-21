"""Cycle146 biome-sensitive trophic capacities: research hypotheses, NOT measured physiology.

Values relate to old synthetic Book units. The same Book accounts own all actual energy.
Protein is a structural/essential nutrient, not a bonus energy token. Carnivores
profit from meat's digestibility, variable lipid content, meal storage, and
specialized hunting, not a universal multiplier to physical calories.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class CarnivoreRole:
    meat_digestibility: float
    stomach_fraction: float
    reserve_days: float
    pursuit_effort: float
    scent_radius: int
    handling_days: float
    carrion_fraction: float
    refuge_sensitivity: float

CARNIVORE_ROLES = {
    'ridge_hound': CarnivoreRole(.86, .43, 38., 1.00, 2, .38, .32, .52),
    'red_fox': CarnivoreRole(.89, .37, 32., .80, 2, .26, .40, .65),
    'golden_jackal': CarnivoreRole(.88, .40, 35., .85, 2, .30, .45, .55),
    'insectivore_shrew': CarnivoreRole(.80, .24, 4., .52, 1, .09, .50, .55),
    'carrion_bird': CarnivoreRole(.85, .31, 16., .72, 2, .22, .80, .50),
}

# These are trophic link preferences, not guaranteed prey or spawning rules.
HABITAT_REFUGE = {'forest':.56,'grassland':.36,'wetland':.61,'floodplain':.43,'ridge':.50}
PREY_SHELTER = {'burrow_rabbit':.48,'field_vole':.52,'field_mouse':.52,
                'meadow_grazer':.08,'forest_browser':.12,'insectivore_shrew':.18,
                'red_fox':.20,'golden_jackal':.17}

# Pseudo-fitness is a relative capture/handling/defence trade-off, not an
# immunity flag. Intraguild attacks are dangerous and nutritionally unreliable.
PREY_PREFERENCE = {
    'ridge_hound': {'field_mouse':.22,'field_vole':.23,'insectivore_shrew':.18,
                    'red_fox':.065,'golden_jackal':.07,'burrow_rabbit':1.10,
                    'meadow_grazer':1.20,'forest_browser':1.05},
    'red_fox': {'field_mouse':1.13,'field_vole':1.19,'burrow_rabbit':.91,
                'insectivore_shrew':.45},
    'golden_jackal': {'field_mouse':.85,'field_vole':.95,'burrow_rabbit':1.05,
                     'insectivore_shrew':.40},
}

@dataclass(frozen=True)
class PlantEaterRole:
    digestibility:float
    gut_fraction:float
    forage_capacity:float

# Synthetic, habitat/plant-food approximations. Herbivores may forage in
# higher volume, but fibrous diets do not acquire an invented calorie premium.
PLANT_EATER_ROLES={
 'field_mouse':PlantEaterRole(.64,.33,.24),
 'meadow_grazer':PlantEaterRole(.60,.43,.22),
 'forest_browser':PlantEaterRole(.59,.42,.20),
 'burrow_rabbit':PlantEaterRole(.63,.43,.25),
 'field_vole':PlantEaterRole(.60,.39,.25),
 'forest_elephant':PlantEaterRole(.50,.62,.18),
 'woolly_mammoth':PlantEaterRole(.51,.64,.17),
}
