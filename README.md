# Computational Total War Analysis

Reproducible analyses derived from the [Computational Total War](https://github.com/OwenTanzer/computational-total-war)
dataset, separated from the production reference source.

## Race tactical possibility space

**Janus Strategic Distance (JSD)** measures continuous relationships among 24
race rosters. Eighteen interpretable capabilities each retain breadth, ceiling,
and multiplayer `cost_access`, producing 54 primary dimensions.

The pipeline reports weighted distances, signed directional contrasts,
nearest neighbors, convex archetypal mixtures, feature-perturbation uncertainty,
and local distinctive options. Archetypes are tactical poles, not race classes.
Their number controls descriptive resolution. A mixture can be stable and broad;
uncertainty is measured separately from mixture entropy.

It evaluates three through eight poles and selects the smallest stable basis
at or after the reconstruction-error knee. If none passes the stated stability
thresholds, it reports that failure and retains the knee basis as **provisional**
diagnostics. It never silently relaxes thresholds to manufacture a selection.

The original capability formulas and distance scale are preserved. Unit tier
remains a separate topology sensitivity, not campaign recruitment access.
These outputs describe roster possibilities, not army usage, win rates or
causal combinations of tactics.

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
seven artifacts in a new temporary directory and compares every byte and the
exact file set with the reviewed snapshot. Use the same numerical-library environment
for exact reproduction; floating-point library/platform changes can affect
nonconvex optimization paths. No persistent server is required for this batch
analysis.
