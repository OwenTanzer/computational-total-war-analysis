# Janus: roster relationships and attainable capability packages

Locked patch 8.1.1; 972 eligible units, 24 races, 54 preserved aggregate dimensions.

## Relationships first

Distances summarize roster profiles. Leading contrasts and local residuals explain their differences; unit evidence identifies the purchases behind the summaries.

| Race | Nearest roster | Distance | Largest local distinction | View | Signed residual |
|---|---|---:|---|---|---:|
| beastmen | wood_elves | 0.8923 | avoidance | breadth | +0.3124 |
| bretonnia | empire | 1.2540 | contact_authority | ceiling | -0.3940 |
| chaos_dwarfs | dark_elves | 1.0028 | bombardment | breadth | +0.4543 |
| daemons_of_chaos | warriors_of_chaos | 1.2826 | command_magic | cost_access | -0.4427 |
| dark_elves | grand_cathay | 0.8917 | morale | breadth | -0.2311 |
| dwarfs | empire | 1.6958 | role_coverage | breadth | -0.5116 |
| empire | grand_cathay | 1.1652 | role_coverage | breadth | -0.3838 |
| grand_cathay | dark_elves | 0.8917 | command_magic | breadth | +0.3216 |
| greenskins | dark_elves | 0.9077 | command_magic | breadth | -0.3288 |
| high_elves | dark_elves | 1.0196 | morale | breadth | +0.3262 |
| khorne | nurgle | 1.2867 | command_magic | cost_access | -0.5903 |
| kislev | wood_elves | 1.0119 | movement | breadth | +0.2712 |
| lizardmen | high_elves | 1.4042 | target_solutions | breadth | +0.3661 |
| norsca | warriors_of_chaos | 0.9990 | role_coverage | breadth | -0.2005 |
| nurgle | kislev | 1.1401 | battlefield_control | breadth | +0.3901 |
| ogre_kingdoms | chaos_dwarfs | 1.0415 | burst | breadth | +0.3620 |
| skaven | greenskins | 1.0428 | contact_authority | breadth | -0.3059 |
| slaanesh | beastmen | 1.1727 | elite_orientation | breadth | +0.4420 |
| tomb_kings | grand_cathay | 1.1033 | morale | breadth | -0.3044 |
| tzeentch | nurgle | 1.2241 | restoration | breadth | +0.4263 |
| vampire_coast | skaven | 1.1920 | morale | cost_access | +0.3863 |
| vampire_counts | norsca | 1.4899 | restoration | breadth | +0.4990 |
| warriors_of_chaos | norsca | 0.9990 | material_durability | ceiling | +0.2246 |
| wood_elves | beastmen | 0.8923 | deployment | breadth | +0.3716 |

Breadth, ceiling and cost access remain separate. Pairwise distances and leading signed contrasts are in `jsd_report.json`; local evidence is in `race_details.json` and contributing unit IDs in `unit_evidence.json`.

## Attainable combinations

2616 race/query families cover every pair of the 15 unit capability proxies, plus raw speed, armour and range comparisons. Each evaluates a 3×3 grid of positive-global-support quantiles (50%, 75%, 90%). Threshold values and their units are published.

One-unit packages require both capabilities in the same purchase. Two-unit packages require distinct providers; the all-units-speed query instead requires both units to meet the speed floor. Cost is summed once per purchase. Scores are never summed into army power.

The package file retains exact cost/capability Pareto frontiers and every minimum-cost tie on the requirement grid. Null cost means unattainable or no positive global support, with an explicit reason. Unit IDs resolve to original keys, costs, measurements and all proxy capabilities.

### Requirement-dependent cost reversals

| Requirement family | Rosters A / B | Requirements favoring A; costs A / B | Requirements favoring B; costs A / B |
|---|---|---|---|
| raw_speed + raw_armour (distinct providers allowed) | beastmen / bretonnia | raw_speed ≥ 9, raw_armour ≥ 50; 1050 / 1100 | raw_speed ≥ 4.8, raw_armour ≥ 50; 750 / 700 |
| raw_armour + raw_range (distinct providers allowed) | beastmen / nurgle | raw_armour ≥ 50, raw_range ≥ 140; 1550 / 1750 | raw_armour ≥ 90, raw_range ≥ 140; 2600 / 1750 |
| raw_speed + raw_range (distinct providers allowed) | beastmen / lizardmen | raw_speed ≥ 7, raw_range ≥ 380; 1950 / 2100 | raw_speed ≥ 4.8, raw_range ≥ 140; 1950 / 850 |
| raw_speed + raw_range (all-unit speed floor) | chaos_dwarfs / daemons_of_chaos | raw_speed ≥ 4.8, raw_range ≥ 140; 575 / 1100 | raw_speed ≥ 4.8, raw_range ≥ 227.5; 2750 / 1100 |
| shock + avoidance (distinct providers allowed) | beastmen / chaos_dwarfs | shock ≥ 0.4595, avoidance ≥ 0.367596; 800 / 1100 | shock ≥ 0.4595, avoidance ≥ 0.196778; 600 / 500 |
| deployment + burst (distinct providers allowed) | beastmen / daemons_of_chaos | deployment ≥ 0.3, burst ≥ 0.424786; 750 / 1150 | deployment ≥ 0.3, burst ≥ 0.310081; 750 / 675 |

Examples prioritize raw-measure families, then proxy families with the most reversals, using distinct race pairs when available. Costs are minimum multiplayer prices with at most two units. These are navigation examples, not prevalence estimates. Exact thresholds, complete cost matrices and all witnesses are retained in the data files.

## Assumptions and consequences

11 of 24 nearest-neighbor identities persist across equal weighting and each of four block-emphasis scenarios. All scenario distances, ranks and changed neighborhoods are retained.

Each emphasis doubles one block relative to the others while retaining the original total squared weight. These scenarios change roster relationships; archetypes are not refitted under them.

## Alternative compressed representations

The reconstruction-error knee is K=5; it is descriptive and excludes no representation. No resolution is selected.

| K | Relative squared error | Optimizer worst-race TV95 | Local mean TV | Local worst-race TV95 | Local worst-pole relative95 | Stress mean TV |
|---|---:|---:|---:|---:|---:|---:|
| 3 | 0.6329 | 0.6501 | 0.1197 | 1.0000 | 0.9648 | 0.2623 |
| 4 | 0.5358 | 0.0006 | 0.0243 | 0.1248 | 0.0691 | 0.2644 |
| 5 | 0.4663 | 0.0010 | 0.0396 | 0.1751 | 0.1208 | 0.2588 |
| 6 | 0.4057 | 1.0000 | 0.0311 | 0.1666 | 0.0933 | 0.2475 |
| 7 | 0.3569 | 1.0000 | 0.0442 | 0.8961 | 0.5737 | 0.2604 |
| 8 | 0.3126 | 1.0000 | 0.0268 | 0.1273 | 0.0767 | 0.2607 |

TV (total variation) measures the fraction of membership mass reassigned. Pole displacement is measured in the original weighted space and normalized by nearest reference-pole separation. These are separate per-race/per-pole percentiles, not simultaneous guarantees for entire runs.

Full memberships, pole profiles, movement distributions, optimizer attempts and profile-change intervals are retained for every K. Adjacent representations have nearest-profile correspondences in both directions, allowing many-to-one matches. Distances, ties and mapped membership changes accompany these correspondences; they do not establish ancestry or a causal split.

### Tolerance comparisons without a winner

| Membership limit | Pole limit | All resolutions within both limits |
|---:|---:|---|
| 0.05 | 0.10 | None |
| 0.05 | 0.25 | None |
| 0.05 | 0.50 | None |
| 0.10 | 0.10 | None |
| 0.10 | 0.25 | None |
| 0.10 | 0.50 | None |
| 0.20 | 0.10 | 4 |
| 0.20 | 0.25 | 4, 5 |
| 0.20 | 0.50 | 4, 5 |
| 0.30 | 0.10 | 4 |
| 0.30 | 0.25 | 4, 5 |
| 0.30 | 0.50 | 4, 5 |

Both unchanged-data optimization and local perturbations must satisfy the illustrative limits with converged fits and distinct reference poles. Structural stress is reported separately. No cutoff is adopted and none of these comparisons chooses K.

## Evidence contract

- `race_capability_views.csv`: preserved breadth, ceiling and cost access.
- `race_capability_composites.csv`: sample-relative display summaries.
- `race_archetype_memberships.csv`: all K/race memberships and diagnostics; blank pole columns mean the pole does not exist at that K.
- `race_details.json`: capability summaries, local residuals and unit-evidence references.
- `jsd_report.json`: pair contrasts, all representations and cross-resolution correspondences.
- `unit_evidence.json`: unit keys, original measurements, scores and aggregate witnesses.
- `capability_packages.json`: exact bounded frontiers, requirement grids, costs and tied witnesses.
- `assumption_sensitivity.json`: block-emphasis relationships and requirement-dependent cost comparisons.
- `unit_tier_sensitivity.json`: unit-classification topology sensitivity.

Primary/unit-tier distance correlation: 0.998457.

These are roster-listed possibilities, not guarantees of faction recruitment legality, playable armies, tactical synergy, win rates or causal strategy modes. Packages contain at most two distinct units. Capability proxies retain their earlier scoring assumptions; raw-measure queries retain missingness. Entropy describes mixing in a fitted basis, not tactical versatility.
