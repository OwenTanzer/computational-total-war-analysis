# Janus Strategic Distance: methodology

## Question and source

How do the tactical possibilities of the 24 playable race rosters relate?
Janus Strategic Distance (JSD) gives both a symmetric distance and a signed
account of what changes between two rosters. It does not measure observed army
composition or play frequency.

The locked CTW source is patch 8.1.1, Steam build 24237342, ultra unit scale,
commit `8c2169b837288d03ba0188b468f06a2f3bcb4b28`. The builder checks the catalog,
requires the exact git commit, and rejects modified tracked source files.

Eligible units are non-characters, not Regiments of Renown, within `race_core`
or `race_core_and_variant`, and have positive multiplayer cost: 972 units.
Generic command/magic metadata retains the existing extractor, including its
Daemons of Chaos fallback when generic rows are absent. This is a provisional
semantic proxy, not a faction-specific campaign model.

## Preserved capabilities

| Block | Features |
|---|---|
| Geometry | movement, deployment, shock, contact authority |
| Damage | melee pressure, missile pressure, bombardment, target solutions, burst, sustain |
| Survival | material durability, avoidance, morale, restoration |
| Architecture | role coverage, elite orientation, battlefield control, command and magic |

`feature_schema.json` specifies ingredients and weights; `race_features.py`
implements them. Positive observations receive percentile ranks within positive
support; structural zeros stay zero. Bombardment requires a missile weapon and
artillery or genuine explosion potency. The refactor preserves all capability
values from the reviewed baseline; a source-backed regression checks them.

Three views remain distinct:

1. **Breadth:** 40% high-capability role/cost-cell coverage, 30% positive unit
   share, 30% share at or above the global positive-score 65th percentile.
2. **Ceiling:** mean of the strongest 8% of eligible units, bounded to 1–3 units.
3. **Cost access:** mean best capability below 12 global multiplayer-cost caps
   spanning the 10th–95th percentiles.

Role coverage, elite orientation and command/magic retain their specialized
view definitions in the schema. The 0–100 composites are sample-relative
summaries: a zero composite denotes the minimum among races, not necessarily
absence of a capability. They are not balance rankings.

## Distance and directional explanation

Standardize each of the 54 primary columns independently. Let z be these
coordinates and q their squared-distance weights. For a feature in a block with
m features, q = view_share / (3m), with view shares 0.50 breadth, 0.25 ceiling,
and 0.25 cost_access. Each block has total weight 1/3; this common scale preserves
the earlier distance values exactly.

```
D(A,B) = sqrt(sum_j q_j * (z_Bj - z_Aj)^2)
delta_j(A -> B) = sqrt(q_j) * (z_Bj - z_Aj)
D(A,B)^2 = sum_j delta_j(A -> B)^2
delta(A -> B) = -delta(B -> A)
```

All 276 unordered pairs retain distance and neighbor rank in both directions.
Their reports display up to four increasing and four decreasing components,
with view, raw difference and squared-distance contribution. The full vector
is accessible through `directional_delta`; leading components alone need not
sum to the full squared distance. Equal-distance ranks use stable race order.

## Unit evidence and bounded capability combinations

Every eligible unit retains a stable (race, unit_key) identity, multiplayer cost,
all 15 unit capability scores, source measurements with missingness, and the
attribute/ability/contact keys used by the scoring proxies. Race-level witnesses
identify positive/high-support units, occupied role/cost cells, ceiling contributors
with their exact equal weights, and all positive-score champions under each cost cap.
The original schema and locked source supply the remaining ingredient definitions.
Role coverage, elite orientation and command/magic are roster metadata and are not
invented as scores for individual package units.

The 15 scores retain the original percentile/flag formulas, including baseline
zero imputation of numeric inputs. They are exploratory capability proxies, not
physical damage or effectiveness estimates. The new raw speed, armour and range
queries use original finite measurements, preserving missingness. Missing raw
requirements cannot be satisfied. Non-missile range is excluded. Source identifiers
allow inspection of the original complete unit record.

For every unordered pair of the 15 proxy capabilities, evaluate both:

- **same_unit:** one unit must supply A and B; count its price once;
- **distinct_providers:** two different units supply A and B respectively; sum
  their prices. No repeated unit types, extra units or additive score aggregation.

There are also three raw-measure pairs (speed/range, armour/range, speed/armour)
and a fourth speed/range query with **all_units_a** semantics: both selected units
must satisfy the speed floor, while at least one supplies the required range.
Its package profile uses minimum speed and maximum range. Distinct-provider
queries require only the designated witness to satisfy each requirement.
The one-unit comparator continues to require both properties in that same unit.

This gives 109 query families per race. Each evaluates all nine combinations of
50th/75th/90th percentiles of global positive finite support, using linear quantile
interpolation. Repeated threshold values are retained explicitly, not treated as
new evidence. A variable without positive support has null thresholds and an
explicit unavailable reason. These thresholds are requirement scenarios, not
significance tests or canonical tactical objectives. Costs and source units are
not aggregated across races.

Enumerate all one-unit and ordered distinct-provider pairs (unordered pairs for
all-units-speed). A package dominates another only if its cost is no greater,
both achieved capabilities are no smaller, and at least one comparison is strict.
A sorted cost/A/B skyline with a prefix-maximum tree computes the exact Pareto
frontier for this bounded model. Preserve every objective-equivalent frontier
witness and every minimum-cost tie on the requirement grid, including cheaper
witnesses that are dominated by stronger packages at the same price. Package
row references identify the exact providers and achieved values. Two possible
provider assignments of the same pair can be distinct evidence rows.

`minimum_cost_at_most_two` is the minimum across the two modes. A supplied budget
is sufficient exactly when it exceeds or equals that cost. Null records distinguish
unattainability in a roster from a variable with no positive global support.
The complete frontiers support requirements beyond the displayed nine points;
the grid retains all cheapest ties, while off-grid queries can use the frontier
for exact minimum cost but may omit equal-cost dominated witnesses.

This is a model of roster-listed access, not faction-specific availability or legal
army composition. Units in race variants may not be jointly recruitable by a
particular lord. Commanders, recruitment restrictions, synergy, formations and
battle outcomes remain outside the package model. A two-unit package is evidence
for a capability combination, not a recommended army.

## Assumption sensitivity

Five distance scenarios retain the original standardized measurements: equal block
weighting and one emphasis per block. An emphasized block receives twice each
other block's squared-distance weight; renormalize to the original total 4/3.
Publish all distance matrices, directional neighbor ranks, four-neighbor retention,
and nearest-neighbor identities. These scenarios test relationship sensitivity;
they do not refit archetypes or demonstrate their robustness to alternative blocks.

For each package family, retain the complete race-by-requirement minimum-cost
matrix, including null unattainability. Enumerate race pairs whose finite cost
ordering reverses across requirements, providing a witness requirement in each
direction. Missing access is visible in the matrix and is not converted to a
numeric rank. A reversal is conditional evidence, not a population statistic.

## Convex archetypal representations

For weighted matrix X, minimize `||X - W H X||²` subject to nonnegative rows
summing to one in both W and H. H builds poles within the convex hull of observed
races; W expresses each race as a mixture of those poles. Unlike unconstrained
factorization, this cannot invent poles outside the observed capability space.

The solver alternates convex projected-gradient subproblems with acceleration,
40 inner iterations, up to 150 outer iterations, and normalized objective-change
tolerance 1e-8. Five seeded starts use probabilistic farthest-point initialization.
We retain the lowest loss and expose every attempt's seed, iteration budget,
start losses and convergence statuses, including initial and retry histories.
The joint problem is nonconvex; convergence does not certify a global optimum.

Evaluate K=3 through K=8. The reference is the lowest-loss result among an
initial five-start fit and eight independent five-start control fits. Reference
identities are ordered deterministically. For a fit that has not converged, retry
with up to 600 outer iterations, starting from that fit plus independent seeds;
unresolved convergence failures remain explicit and prevent a representation
from satisfying a tolerance comparison when they occur in its reference, controls
or local robustness trials. Every K retains full reference profiles, memberships
and diagnostic distributions; no representation is privileged.

Normalize the endpoint-to-endpoint gain in reconstruction error and K to [0,1];
the knee is the maximum gain above the straight endpoint chord. The knee remains
a descriptive compression choice. It alone does not establish robustness.

## Three distinct diagnostic regimes

1. **Optimization repeatability:** eight independent five-start fits to unchanged
   weighted data, with no reference warm start. This measures sensitivity to the
   search procedure. Because the reference is the best of these and an initial
   fit, the comparison is to the best available solution, not a global-optimum claim.
2. **Local robustness:** 40 runs retain all 54 coordinates. Apply Normal(1, 0.08)
   multipliers (floor 1e-6 to retain support) and renormalize squared weights within
   each block to preserve its exact original total. Each fit has five starts,
   one at the reference and four independently initialized.
3. **Structural stress:** 40 runs resample feature-view dimensions with replacement
   and apply independent Normal(1, 0.08) multipliers. Omitted dimensions and changed
   block emphases are deliberate. This measures dependence on the measurement
   system and is excluded from tolerance comparisons.

Draws are seeded and paired across resolutions. Each regime is summarized
separately; the perturbation fits can still include search effects, so these
regimes are diagnostics, not an additive variance decomposition.

### Comparable membership movement

Use total variation distance: `TV(w,w') = 0.5 * sum_k abs(w_k-w'_k)`.
It lies in [0,1] and measures the fraction of mixture mass reassigned. Moving 20
percentage points between two poles gives 0.20 with either three or eight poles.
Adding unused coordinates cannot dilute the score. Retain each race's complete
run distribution, mean, 95th percentile and maximum, plus aggregate summaries.

Membership coefficient means, standard deviations and 5th/95th percentiles are
reported separately for each regime. Normalized reference entropy
`-sum(w log w)/log(K)` still measures breadth of mixing within this fitted basis;
it is not a measure of overall tactical versatility or perturbation uncertainty.

### Pole identity and capability-profile movement

Match each trial's poles to the reference by Hungarian assignment in the original
weighted space, using H X rather than the perturbed coordinates. Retain matched
memberships AND pole positions. For each pole, report the complete distribution
of Euclidean displacement, its mean, 95th percentile and maximum. Also normalize
by distance to the nearest other reference pole to express movement relative
to the separation of their identities. Coincident reference poles make this ratio
undefined: record a degeneracy flag and fail the pole-tolerance comparison explicitly.

For every basis, every regime retains the full 54-coordinate mean, standard
deviation and 5th/95th percentile of weighted capability-profile changes. Coordinates
follow `profile_dimensions`. Movement-distribution columns follow the reported race
and pole order. Label matching resolves permutations; it does not erase pole drift.

### Tolerance comparisons and correspondences

There is no selected resolution, adopted tolerance, or privileged error-knee basis.
The output status is `multiple_descriptive_representations`. The knee remains a
compression descriptor; smaller resolutions remain in all comparisons. The former
selection fields and tolerance-adoption command-line flags are removed.

A 12-cell tolerance grid crosses membership limits 0.05, 0.10, 0.20, 0.30 with pole
limits 0.10, 0.25, 0.50. Report every K's pass/fail and reasons. BOTH optimization
repeatability and local robustness must meet each race's 95th-percentile total
variation and each pole's 95th-percentile relative displacement, with converged
fits and nondegenerate poles. Structural stress is excluded. These separate
percentiles do not guarantee that a whole run is within both limits 95% of the
time. Maximum movements and complete run distributions remain visible.

For adjacent tested resolutions retain the full profile-distance matrix and each
pole's nearest counterpart in both directions. This permits many-to-one links.
Record all distance ties (absolute tolerance 1e-12), choosing the lowest index for
membership mapping. Sum source memberships into their nearest destination poles
and report the resulting per-race total variation against destination memberships.
A nearest-profile correspondence is descriptive: it does not establish descent,
causal splitting or semantic equivalence. Tied mappings have no unique identity.

The intervals concern method sensitivity, not sampled battles. Feature views are
correlated and structural resampling is a stress intervention. Eight optimization
controls cannot establish rare-failure rates; one control can be its own reference.

## Local distinctiveness

For each race, take its four nearest other races and compute their inverse-distance
weighted mean. Subtract this mean from the focal race in the original weighted
space. Retain the complete signed residual and leading positive/negative raw and
weighted components. If a neighbor has identical coordinates, only zero-distance
neighbors receive equal weight. Self is always excluded explicitly.

## Unit-tier sensitivity

Add 15 `main_units.tier` frontier views only for sensitivity, splitting each
unit-derived feature's access share into 0.125 cost and 0.125 tier. The primary
54 dimensions do not change. Report distance-matrix correlation, nearest-neighbor
changes, distance-profile shifts and leading directional changes for each race's
most affected pair. This does not fit a second archetypal model. Tier classification
does not encode buildings, resources, technologies, landmarks, scripted pools or
campaign starting conditions.

## Limits and reproduction

These are static roster affordances. Formation geometry, collision and animation,
projectile obstruction, micro burden, fatigue, terrain, lord and technology effects,
campaign recruitment and actual outcomes remain outside scope. Semantic attribute
and magic mappings are provisional. Larger rosters can affect breadth despite
role/cost-cell normalization. Capability combinations are not a causal theory of
strategy; interpretation must investigate the interactions separately.

Run `python -m ctw_analysis.build_race_strategy_space --ctw-root PATH`.
`--workers N` evaluates independent resolutions in separate processes with fixed
per-resolution seeds; worker count does not change the outputs. Use single-thread
numerical libraries within each worker.
Generated intermediates belong in ignored `work/`. Reviewed results contain exactly
ten files. `--verify-regeneration` rebuilds in a clean temporary directory and
compares file sets and every byte. Seeded output is deterministic within a fixed
runtime using single-thread numerical libraries; differing libraries/platforms
may change optimization paths. The source-backed tests independently compare
all capability values with the pre-refactor reviewed snapshot.
