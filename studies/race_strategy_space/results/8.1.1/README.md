# Janus Strategic Distance: patch 8.1.1

Source: `8c2169b837288d03ba0188b468f06a2f3bcb4b28`; 972 eligible units; 54 primary dimensions across 24 races.

Error knee: K=5. Reported basis: K=5 (provisional_error_knee_basis).
Selection status: tolerances_not_adopted; selected resolution: None.
No numerical tolerance is adopted by default. The table below shows conditional choices; it does not declare natural strategic classes.

## Separate diagnostics

| K | Relative squared error | Optimizer worst race TV95 | Local mean TV | Local worst race TV95 | Local worst pole relative95 | Stress mean TV |
|---|---:|---:|---:|---:|---:|---:|
| 3 | 0.6329 | 0.6501 | 0.1197 | 1.0000 | 0.9648 | 0.2623 |
| 4 | 0.5358 | 0.0006 | 0.0243 | 0.1248 | 0.0691 | 0.2644 |
| 5 | 0.4663 | 0.0010 | 0.0396 | 0.1751 | 0.1208 | 0.2588 |
| 6 | 0.4057 | 1.0000 | 0.0311 | 0.1666 | 0.0933 | 0.2475 |
| 7 | 0.3569 | 1.0000 | 0.0442 | 0.8961 | 0.5737 | 0.2604 |
| 8 | 0.3126 | 1.0000 | 0.0268 | 0.1273 | 0.0767 | 0.2607 |

TV is total variation distance: the fraction of membership mass reassigned. TV95 is the 95th percentile across runs for each race; worst means the largest of those race-specific values. Pole displacement is divided by separation from the nearest other reference pole.

Optimization repeats use unchanged data and independent starts. Local robustness retains every dimension and equal block totals. Structural stress resamples dimensions and reweights blocks; it never gates selection.

## Conditional tolerance choices

| Maximum worst-race TV95 | Maximum worst-pole relative95 | Smallest qualifying K at/after knee |
|---:|---:|---:|
| 0.05 | 0.10 | None |
| 0.05 | 0.25 | None |
| 0.05 | 0.50 | None |
| 0.10 | 0.10 | None |
| 0.10 | 0.25 | None |
| 0.10 | 0.50 | None |
| 0.20 | 0.10 | None |
| 0.20 | 0.25 | 5 |
| 0.20 | 0.50 | 5 |
| 0.30 | 0.10 | None |
| 0.30 | 0.25 | 5 |
| 0.30 | 0.50 | 5 |

Both optimization repeatability and local robustness must satisfy both tolerances, with all reference/control/local fits converged. Structural stress is excluded. A membership tolerance of 0.20 allows 20 percentage points to move; a pole tolerance of 0.25 allows movement of one quarter of nearest-pole separation. These are interpretable policy choices, not significance thresholds.

## Reported poles

- **A1** — leading memberships: ogre_kingdoms 1.000, chaos_dwarfs 0.989, dark_elves 0.754. Leading coordinates: contact_authority__breadth +0.293, burst__breadth +0.199, sustain__breadth +0.148, role_coverage__breadth +0.148.
- **A2** — leading memberships: daemons_of_chaos 1.000, warriors_of_chaos 0.846, khorne 0.722. Leading coordinates: material_durability__breadth +0.294, movement__breadth +0.245, shock__breadth +0.241, restoration__breadth +0.219.
- **A3** — leading memberships: dwarfs 1.000, bretonnia 0.837, empire 0.742. Leading coordinates: role_coverage__breadth -0.402, battlefield_control__breadth -0.320, role_coverage__cost_access -0.304, contact_authority__breadth -0.298.
- **A4** — leading memberships: beastmen 0.918, wood_elves 0.855, slaanesh 0.845. Leading coordinates: deployment__breadth +0.431, avoidance__breadth +0.352, sustain__breadth -0.193, movement__breadth +0.183.
- **A5** — leading memberships: vampire_coast 0.966, vampire_counts 0.888, skaven 0.770. Leading coordinates: morale__breadth -0.352, shock__breadth -0.257, morale__ceiling -0.253, burst__breadth -0.248.

## Pole movement in the reported basis

| Regime | Pole | Mean displacement | Largest displacement | Relative 95th percentile |
|---|---|---:|---:|---:|
| optimization_repeatability | A1 | 0.0004 | 0.0007 | 0.0005 |
| optimization_repeatability | A2 | 0.0004 | 0.0007 | 0.0006 |
| optimization_repeatability | A3 | 0.0001 | 0.0001 | 0.0001 |
| optimization_repeatability | A4 | 0.0001 | 0.0002 | 0.0001 |
| optimization_repeatability | A5 | 0.0003 | 0.0006 | 0.0004 |
| local_robustness | A1 | 0.0523 | 0.1363 | 0.0790 |
| local_robustness | A2 | 0.0625 | 0.3954 | 0.1035 |
| local_robustness | A3 | 0.0657 | 0.9494 | 0.0696 |
| local_robustness | A4 | 0.1076 | 1.6280 | 0.1208 |
| local_robustness | A5 | 0.0538 | 0.2624 | 0.0781 |
| structural_stress | A1 | 0.3948 | 1.1363 | 0.6198 |
| structural_stress | A2 | 0.3275 | 0.6877 | 0.5128 |
| structural_stress | A3 | 0.4235 | 0.9736 | 0.6613 |
| structural_stress | A4 | 0.5869 | 1.7374 | 1.4320 |
| structural_stress | A5 | 0.4759 | 1.4230 | 0.7995 |

## Local neighborhoods

| Race | Nearest race | Distance | Entropy | Local mean TV | Local TV95 |
|---|---|---:|---:|---:|---:|
| beastmen | wood_elves | 0.8923 | 0.176 | 0.054 | 0.077 |
| bretonnia | empire | 1.2540 | 0.327 | 0.064 | 0.093 |
| chaos_dwarfs | dark_elves | 1.0028 | 0.038 | 0.014 | 0.046 |
| daemons_of_chaos | warriors_of_chaos | 1.2826 | -0.000 | 0.000 | 0.000 |
| dark_elves | grand_cathay | 0.8917 | 0.347 | 0.029 | 0.057 |
| dwarfs | empire | 1.6958 | -0.000 | 0.000 | 0.000 |
| empire | grand_cathay | 1.1652 | 0.355 | 0.051 | 0.072 |
| grand_cathay | dark_elves | 0.8917 | 0.620 | 0.057 | 0.124 |
| greenskins | dark_elves | 0.9077 | 0.823 | 0.056 | 0.129 |
| high_elves | dark_elves | 1.0196 | 0.510 | 0.044 | 0.093 |
| khorne | nurgle | 1.2867 | 0.367 | 0.017 | 0.044 |
| kislev | wood_elves | 1.0119 | 0.715 | 0.065 | 0.105 |
| lizardmen | high_elves | 1.4042 | 0.580 | 0.077 | 0.145 |
| norsca | warriors_of_chaos | 0.9990 | 0.712 | 0.040 | 0.072 |
| nurgle | kislev | 1.1401 | 0.869 | 0.058 | 0.123 |
| ogre_kingdoms | chaos_dwarfs | 1.0415 | -0.000 | 0.003 | 0.019 |
| skaven | greenskins | 1.0428 | 0.353 | 0.054 | 0.175 |
| slaanesh | beastmen | 1.1727 | 0.268 | 0.060 | 0.092 |
| tomb_kings | grand_cathay | 1.1033 | 0.419 | 0.030 | 0.070 |
| tzeentch | nurgle | 1.2241 | 0.649 | 0.037 | 0.072 |
| vampire_coast | skaven | 1.1920 | 0.091 | 0.029 | 0.063 |
| vampire_counts | norsca | 1.4899 | 0.218 | 0.033 | 0.112 |
| warriors_of_chaos | norsca | 0.9990 | 0.334 | 0.039 | 0.093 |
| wood_elves | beastmen | 0.8923 | 0.257 | 0.040 | 0.068 |

## File contract

- `race_capability_views.csv`: original breadth, ceiling and cost_access measurements.
- `race_capability_composites.csv`: sample-relative 0–100 summaries; zero denotes the sample minimum.
- `race_archetype_memberships.csv`: reference weights, entropy, and explicitly named statistics for each of the three diagnostic regimes.
- `race_details.json`: capability evidence and local residuals against four distance-weighted neighbors.
- `jsd_report.json`: all pair comparisons, per-resolution diagnostics, conditional tolerance choices, and full movement distributions and profile-change intervals for the reported basis. Distribution columns follow `races`, pole IDs and `profile_dimensions`.
- `unit_tier_sensitivity.json`: topology changes only; unit tier does not establish campaign recruitment access.

Primary/sensitivity distance correlation: 0.998457.

Pair records show up to four components per sign. Reversing the pair negates its components and exchanges ranks. Use `directional_delta` for the exact full-vector decomposition.

Entropy describes mixing within the fitted basis, not overall tactical versatility. Pole movement and profile changes are measured in the original weighted space after label alignment. Tail events and failed optimization runs remain visible, even when a percentile tolerance accepts a representation.

The measurements concern static roster possibilities and method sensitivity, not observed armies, causal tactical combinations, win rates, or confidence intervals over battles.
