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

Evaluate K=3 through K=8. Normalize the endpoint-to-endpoint gain in reconstruction
error and K to [0,1]; the knee is the maximal gain above the straight endpoint
chord (ties choose smaller K). The stability rule is fixed at global membership
root mean squared error <=0.12 and maximum per-race error <=0.25. Select the
smallest stable K at or after the knee. These are explicit analytical tolerances,
not statistical significance thresholds. Per-coordinate errors depend on K;
inspect the whole resolution table rather than treating its Boolean flags as facts
about natural classes.

If none qualifies, `selected_resolution` is null. The knee basis is still reported
for inspection, explicitly marked `provisional_error_knee_basis`. This preserves
useful fitted weights without asserting that stable archetypes have been found.

## Perturbation uncertainty and hybridity

Use 40 seeded feature-resampling runs. Resample 54 feature-view columns with
replacement: multiply each original weighted column by sqrt(multinomial count)
and independent Normal(1, 0.08) noise. Use the same draws across resolutions.
This changes the effective feature emphasis, including dropping dimensions;
it is more demanding than testing numerical noise alone.

Each perturbed fit uses two starts, one at the reference fit and one independently
seeded. Match fitted poles to reference poles by Hungarian assignment of distances
between H X positions in the original unperturbed space. Report membership means,
standard deviations, 5th/95th percentiles and deviations from reference weights.
Label matching resolves permutations, not substantive pole drift.

Normalized membership entropy `-sum(w log w)/log(K)` measures the breadth of the
reference mixture. It is distinct from perturbation uncertainty: a consistent
50/50 hybrid has high entropy and zero variance. These intervals concern feature
sensitivity, not population sampling or outcomes of battles. Feature dimensions
are correlated and are not assumed to be independent biological observations.

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
Generated intermediates belong in ignored `work/`. Reviewed results contain exactly
seven files. `--verify-regeneration` rebuilds in a clean temporary directory and
compares file sets and every byte. Seeded output is deterministic within a fixed
runtime using single-thread numerical libraries; differing libraries/platforms
may change optimization paths. The source-backed tests independently compare
all capability values with the pre-refactor reviewed snapshot.
