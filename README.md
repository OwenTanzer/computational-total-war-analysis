# Computational Total War Analysis

Reproducible analyses derived from the [Computational Total War](https://github.com/OwenTanzer/computational-total-war)
dataset, separated from the production reference source.

## Race tactical possibility space

**Janus Strategic Distance (JSD)** measures continuous relationships among 24
race rosters. Eighteen interpretable capabilities each retain breadth, ceiling,
and multiplayer `cost_access`, producing 54 primary dimensions.

The report begins with race neighborhoods, signed contrasts and local distinctive
capabilities. Unit evidence connects these summaries to original unit keys,
measurements, costs and capability scores.

Exact one/two-unit package frontiers compare capabilities in a single purchase
with capabilities supplied by distinct units. A published requirement grid spans
all 105 pairs of unit capability proxies plus four raw-measure queries. Costs,
all cheapest grid ties and stronger Pareto alternatives remain inspectable.
An all-unit speed floor is distinct from merely including one fast unit.

All archetypal resolutions K=3–8 retain profiles, memberships and uncertainty.
There is no winning resolution; the reconstruction knee is descriptive only.
Original-space profile correspondences allow many-to-one links across resolutions.
Optimization repeatability, local robustness and structural stress remain separate,
with full attempt histories and illustrative tolerance comparisons for every K.

Block-emphasis scenarios expose changing roster relationships, and requirement
sweeps expose changing package costs. The original aggregate capability formulas
and distance scale are preserved. Unit tier remains a topology sensitivity.
These are roster-listed possibilities, not faction recruitment guarantees,
recommended armies, win rates or demonstrated tactical synergy.

See [methodology](studies/race_strategy_space/methodology.md),
[interpretation](studies/race_strategy_space/interpretation.md), and
[reviewed results](studies/race_strategy_space/results/8.1.1/README.md).

## Reproduce

Use Python 3.11+ and a clean CTW checkout at the exact commit in `source_lock.json`.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m ctw_analysis.build_race_strategy_space \
  --ctw-root ../computational-total-war
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m ctw_analysis.build_race_strategy_space \
  --ctw-root ../computational-total-war --verify-regeneration
CTW_TEST_ROOT=../computational-total-war python -m unittest discover -s tests -v
```

The default output is `work/janus_output/`. The regeneration gate builds all
ten artifacts in a new temporary directory and compares every byte and the
exact file set with the reviewed snapshot. Use the same numerical-library environment
for exact reproduction; floating-point library/platform changes can affect
nonconvex optimization paths. No persistent server is required for this batch
analysis.
