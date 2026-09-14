# Janus Strategic Distance: patch 8.1.1

Source: `8c2169b837288d03ba0188b468f06a2f3bcb4b28`; 972 eligible units; 54 primary dimensions across 24 races.

Error knee: K=5. Selected resolution: None.
Reported membership basis: K=5 (provisional_error_knee_basis).
K controls descriptive resolution; poles are mixtures within the observed roster space.

| K | Relative squared error | Membership RMSE | Largest race RMSE | Stable |
|---|---:|---:|---:|---|
| 3 | 0.6329 | 0.2744 | 0.4535 | False |
| 4 | 0.5358 | 0.2129 | 0.3207 | False |
| 5 | 0.4663 | 0.1801 | 0.2699 | False |
| 6 | 0.4057 | 0.1549 | 0.2536 | False |
| 7 | 0.3569 | 0.1325 | 0.2105 | False |
| 8 | 0.3126 | 0.1434 | 0.2252 | False |

RMSE means root mean squared error in membership weights. Feature perturbation uncertainty is separate from normalized membership entropy, which measures mixture breadth.

## Derived poles

- **A1** — leading memberships: ogre_kingdoms 1.000, chaos_dwarfs 0.989, dark_elves 0.754. Leading coordinates: contact_authority__breadth +0.293, burst__breadth +0.199, sustain__breadth +0.148, role_coverage__breadth +0.148.
- **A2** — leading memberships: daemons_of_chaos 1.000, warriors_of_chaos 0.846, khorne 0.722. Leading coordinates: material_durability__breadth +0.294, movement__breadth +0.245, shock__breadth +0.241, restoration__breadth +0.219.
- **A3** — leading memberships: dwarfs 1.000, bretonnia 0.837, empire 0.742. Leading coordinates: role_coverage__breadth -0.402, battlefield_control__breadth -0.320, role_coverage__cost_access -0.304, contact_authority__breadth -0.298.
- **A4** — leading memberships: beastmen 0.918, wood_elves 0.855, slaanesh 0.845. Leading coordinates: deployment__breadth +0.431, avoidance__breadth +0.352, sustain__breadth -0.193, movement__breadth +0.183.
- **A5** — leading memberships: vampire_coast 0.967, vampire_counts 0.888, skaven 0.770. Leading coordinates: morale__breadth -0.352, shock__breadth -0.257, morale__ceiling -0.253, burst__breadth -0.248.

## Local neighborhoods

| Race | Nearest race | Distance | Entropy | Membership RMSE |
|---|---|---:|---:|---:|
| beastmen | wood_elves | 0.8923 | 0.176 | 0.211 |
| bretonnia | empire | 1.2540 | 0.327 | 0.270 |
| chaos_dwarfs | dark_elves | 1.0028 | 0.038 | 0.121 |
| daemons_of_chaos | warriors_of_chaos | 1.2826 | -0.000 | 0.017 |
| dark_elves | grand_cathay | 0.8917 | 0.347 | 0.158 |
| dwarfs | empire | 1.6958 | -0.000 | 0.105 |
| empire | grand_cathay | 1.1652 | 0.355 | 0.228 |
| grand_cathay | dark_elves | 0.8917 | 0.620 | 0.193 |
| greenskins | dark_elves | 0.9077 | 0.823 | 0.157 |
| high_elves | dark_elves | 1.0196 | 0.510 | 0.166 |
| khorne | nurgle | 1.2867 | 0.367 | 0.222 |
| kislev | wood_elves | 1.0119 | 0.715 | 0.150 |
| lizardmen | high_elves | 1.4042 | 0.580 | 0.208 |
| norsca | warriors_of_chaos | 0.9990 | 0.712 | 0.148 |
| nurgle | kislev | 1.1401 | 0.869 | 0.183 |
| ogre_kingdoms | chaos_dwarfs | 1.0415 | -0.000 | 0.135 |
| skaven | greenskins | 1.0428 | 0.352 | 0.187 |
| slaanesh | beastmen | 1.1727 | 0.268 | 0.191 |
| tomb_kings | grand_cathay | 1.1033 | 0.419 | 0.159 |
| tzeentch | nurgle | 1.2241 | 0.649 | 0.140 |
| vampire_coast | skaven | 1.1920 | 0.091 | 0.211 |
| vampire_counts | norsca | 1.4899 | 0.218 | 0.233 |
| warriors_of_chaos | norsca | 0.9990 | 0.333 | 0.196 |
| wood_elves | beastmen | 0.8923 | 0.257 | 0.161 |

## Reading the files

- `race_capability_views.csv`: original breadth, ceiling, and cost_access measurements.
- `race_capability_composites.csv`: sample-relative 0–100 summaries; zero means the sample minimum, not absence.
- `race_archetype_memberships.csv`: fitted weights, perturbation means, standard deviations, 5th/95th percentiles, entropy and membership RMSE.
- `race_details.json`: underlying capability evidence and local residuals against four distance-weighted neighbors.
- `jsd_report.json`: all unordered pair distances, neighbor ranks in both directions, leading signed components, resolution audit and pole coordinates.
- `unit_tier_sensitivity.json`: topology changes only; unit tier does not establish campaign recruitment access.

Primary/sensitivity distance correlation: 0.998457.

Pair records give up to four positive and four negative components for the documented from→to direction. Reversing a pair negates its components and exchanges its neighbor ranks. The full 54-component decomposition is available through `directional_delta`; it is not approximated by summing the displayed leading components.

Archetypes summarize static roster possibilities. They do not estimate played army compositions, win rates, or causal tactical combinations. Feature perturbations are sensitivity intervals, not confidence intervals over sampled battles.
