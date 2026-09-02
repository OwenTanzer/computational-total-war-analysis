# Agent guide

This repository is the experimental analysis layer for
`OwenTanzer/computational-total-war` (CTW). Treat CTW as a read-only data
dependency. Do not copy analysis code or work-in-progress outputs back into the
CTW production dataset unless the user explicitly asks for a mature, validated
artifact to be promoted.

## Boundaries

- Read the CTW checkout named by `source_lock.json` and verify its snapshot.
- Put reusable analysis code in `src/`.
- Put a study's methodology, compact results, and figures under `studies/`.
- Put regenerable unit-level tables, experiments, caches, and notebooks under
  ignored `work/` paths.
- Never edit CTW files under `data/`; stable database keys remain canonical.
- Preserve CTW caveats: blank is not zero, and unit-card statistics exclude
  technologies, skills, lord effects, difficulty, fatigue, terrain, temporary
  abilities, and mods unless a study explicitly models them.

## Race strategy-space study

Start with `studies/race_strategy_space/methodology.md`, then inspect
`feature_schema.json` and the patch-specific files under `results/`. Rebuild
with:

```bash
python src/ctw_analysis/race_feature_analysis.py \
  --ctw-root ../computational-total-war
```

Interpret the clusters as a lossy view of an overlapping feature space. The
low silhouette score is evidence against treating cluster labels as rigid race
classes.

