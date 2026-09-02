# Computational Total War Analysis

Experimental, reproducible analyses derived from the
[Computational Total War](https://github.com/OwenTanzer/computational-total-war)
datasets live here, separately from the production context source.

This separation keeps working hypotheses, provisional metrics, generated
tables, and exploratory clustering from becoming retrieval noise for agents
that use CTW as an authoritative dataset.

## Current study: race strategy space

The first study asks whether the 24 playable races occupy distinct strategic
groups on the battlefield. It represents each race with 18 interpretable
features. Every feature retains three views:

- **Breadth:** how much of the roster can express the capability.
- **Ceiling:** how strong the best options are.
- **Access:** how early the capability appears along the cost frontier.

That produces a 54-dimensional race representation. Equal-weighted feature
blocks prevent a larger block from dominating the distance metric; breadth
receives half of each feature's weight, while ceiling and access receive one
quarter each.

The current result is deliberately nuanced: the best tested hard partition is
seven clusters, but its silhouette is only **0.091**. The useful object is the
continuous neighborhood structure and its bridge cases, not a rigid taxonomy.

See [`studies/race_strategy_space/methodology.md`](studies/race_strategy_space/methodology.md)
for the specification and [`studies/race_strategy_space/results/8.1.1/`](studies/race_strategy_space/results/8.1.1/)
for the committed outputs.

## Reproduce

Place this repository beside a CTW checkout locked to the commit in
`source_lock.json`, then run:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python src/ctw_analysis/race_feature_analysis.py \
  --ctw-root ../computational-total-war
```

Generated files go to `work/race_feature_output/`. The compact, reviewed
snapshot under `studies/` is committed; the 1.2 MB unit-level score table and
other regenerable intermediates remain ignored.

