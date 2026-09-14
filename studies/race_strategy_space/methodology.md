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

## Convex archetypal representation

For weighted matrix X, minimize `||X - W H X||²` subject to nonnegative rows
summing to one in both W and H. H builds poles within the convex hull of observed
races; W expresses each race as a mixture of those poles. Unlike unconstrained
factorization, this cannot invent poles outside the observed capability space.

The solver alternates convex projected-gradient subproblems with acceleration,
40 inner iterations, up to 150 outer iterations, and normalized objective-change
tolerance 1e-8. Five seeded starts use probabilistic farthest-point initialization.
We retain the lowest loss and expose every start's loss and convergence status.
The joint problem is nonconvex; convergence does not certify a global optimum.

Evaluate K=3 through K=8. The reference is the lowest-loss result among an
initial five-start fit and eight independent five-start control fits. Reference
identities are ordered deterministically. For a fit that has not converged, retry
with up to 600 outer iterations, starting from that fit plus independent seeds;
unresolved convergence failures remain explicit and block conditional selection
when they occur in reference, optimization control or local robustness.

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
   system and never gates conditional selection.

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
undefined: record a degeneracy flag and reject conditional selection explicitly.

For the reported basis, every regime retains the full 54-coordinate mean, standard
deviation and 5th/95th percentile of weighted capability-profile changes. Coordinates
follow `profile_dimensions`. Movement-distribution columns follow the reported race
and pole order. Label matching resolves permutations; it does not erase pole drift.

### Explicit tolerance choices

The default build does not adopt a scientific cutoff. It reports the error-knee
basis provisionally and leaves `selected_resolution` null with the distinct status
`tolerances_not_adopted`. This must not be described as failing a stability test.

A 12-cell tolerance grid crosses membership limits 0.05, 0.10, 0.20, 0.30 with pole
limits 0.10, 0.25, 0.50. Each cell selects the smallest K at or after the knee for
which BOTH optimization repeatability and local robustness satisfy:

- every race's 95th-percentile total variation is within the membership limit;
- every pole's 95th-percentile relative displacement is within the pole limit;
- all reference/control/local fits converge and reference poles are nondegenerate.

Stress outcomes are excluded. Maximum observed movements remain visible because
percentile acceptance can tolerate rare jumps. The membership limit describes
mass reallocation; the pole limit describes a fraction of nearest-pole separation.
These are analytical policies, not significance thresholds. Controlled tests
establish their meaning: 20-point transfers are padding invariant, permutations
change nothing, and shifting fixed-membership poles by one quarter of their
separation produces zero membership change but relative pole movement of 0.25.

To adopt a policy explicitly, supply BOTH `--membership-tolerance` and
`--pole-tolerance`. The report records them, and selects a qualifying basis or
returns the distinct status `no_qualifying_resolution`. With no adopted policy,
conditional choices remain reviewable without manufacturing one canonical answer.

The intervals concern method sensitivity, not a population of sampled battles.
Feature views are correlated, and structural resampling is a stress intervention.

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
seven files. `--verify-regeneration` rebuilds in a clean temporary directory and
compares file sets and every byte. Seeded output is deterministic within a fixed
runtime using single-thread numerical libraries; differing libraries/platforms
may change optimization paths. The source-backed tests independently compare
all capability values with the pre-refactor reviewed snapshot.
