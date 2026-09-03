# Race strategy space: methodology

## Question

Do the 24 playable races in *Total War: WARHAMMER III* occupy distinct
battlefield-strategy groups?

The study does not begin by assigning archetypes. It first constructs an
interpretable feature space, then tests how much hard clustering that space can
support. The design intentionally straddles symmetry and asymmetry:

- every race is measured on the same 18 features, enabling comparison;
- every primary feature retains breadth, ceiling, and multiplayer-cost access,
  preventing a single roster average from erasing asymmetric specialists or
  structural gaps.

## Source and scope

The source is CTW patch 8.1.1, Steam build 24237342, unit scale ultra, at the
exact commit recorded in `source_lock.json`.

Eligible units satisfy all of the following:

- category is not `character`;
- unit is not a Regiment of Renown;
- `roster_scope` is `race_core` or `race_core_and_variant`;
- multiplayer cost is positive.

This yields 972 units. Generic, recruitable character skill trees contribute
only to `command_magic`; legendary lords and unique agents are excluded so the
representation remains race-level rather than faction-level.

## Feature model

The 18 features are divided into four conceptual blocks:

| Block | Features |
|---|---|
| Geometry | movement, deployment, shock, contact authority |
| Damage | melee pressure, missile pressure, bombardment, target solutions, burst, sustain |
| Survival | material durability, avoidance, morale, restoration |
| Architecture | role coverage, elite orientation, battlefield control, command and magic |

The exact ingredients and weights are declared in `feature_schema.json` and
implemented in `src/ctw_analysis/race_feature_analysis.py`. Positive raw
continuous statistics are transformed to percentile ranks among positive
observations before they enter unit-level feature formulas. Structural zeros
remain zero rather than acquiring a tied percentile. This makes unlike database
measures comparable without claiming that, for example, one point of speed is
literally equivalent to one point of armour.

### Capability views

For each unit-derived feature and race:

1. **Breadth** combines high-capability role/cost-cell coverage (40%), the
   share of units with any capability (30%), and the share above the global
   positive-unit 65th percentile (30%).
2. **Ceiling** is the mean of the strongest 8% of the race's eligible units,
   capped at three units and floored at one.
3. **Cost access** is the mean best capability available below each of 12 global
   multiplayer-cost caps spanning the 10th through 95th percentiles.

`role_coverage`, `elite_orientation`, and `command_magic` use semantically
equivalent three-view representations specialized to those concepts.

### Unit-tier sensitivity

An optional sensitivity adds the mean best capability available at or below
each `main_units.tier` value from 1 through 5 for the 15 unit-derived features.
This field classifies a unit; it does **not** encode when or how a commander can
recruit it. Special-pool and otherwise gated units can carry ordinary tier
values, so this view is excluded from the primary representation and must not
be interpreted as campaign access.

Exact building-to-unit junctions, technologies, resources, landmarks,
scripted pools, and starting-settlement state are not available in the locked
CTW snapshot. The missing source topology is tracked in
[computational-total-war#1](https://github.com/OwenTanzer/computational-total-war/issues/1).

## Comparison and clustering

The 54 primary columns are standardized independently. Each of the four
conceptual blocks then receives equal total weight. Within a feature, breadth
receives 50% of the squared-distance contribution, while ceiling and cost
access receive 25% each. In the separate 69-column unit-tier sensitivity, the
access quarter is split evenly between multiplayer cost and unit tier.

Ward hierarchical solutions are evaluated for 4 through 8 clusters using the
silhouette score. The best candidate is then stress-tested with 500 seeded
K-means perturbations. Each run samples 80% of feature dimensions and applies
independent multiplicative noise drawn from `Normal(1, 0.08)`. Pairwise
co-clustering frequencies form a consensus distance matrix, which is clustered
with average linkage.

## Current result

Eight clusters narrowly maximize silhouette among the tested primary
solutions, with a score of 0.1203. Scores for 4 through 8 clusters all lie
between 0.103 and 0.120. The unit-tier sensitivity also selects eight clusters
at 0.1226.
This is not evidence for eight natural, well-separated classes. It remains
evidence for an overlapping strategic space with locally useful neighborhoods
and bridge cases.

The stable output should therefore be read in this order:

1. feature views and composites;
2. nearest-neighbor distances and consensus frequencies;
3. cluster labels as a compact summary only.

## Known limits

This is a static roster-capability analysis. It does not currently measure
campaign access. Unit tier is retained only as a non-primary sensitivity and is
not a substitute for building, technology, resource, landmark, scripted-pool,
or starting-state recruitment gates. The study also does not directly observe
formation geometry, collision and animation behavior, projectile obstruction,
micro burden, fatigue, terrain, technologies, campaign skills, lord effects,
difficulty modifiers, or live battle outcomes. Database keywords used for
contact effects and generic magic categories are provisional semantic mappings.
Large DLC-expanded rosters can express breadth differently from smaller
rosters, even with role/cost-cell normalization.

These omissions are reasons to preserve the full feature representation, not
reasons to replace it with hand-authored archetype labels.
