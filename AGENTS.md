# Agent guide

This is the experimental analysis layer for
`OwenTanzer/computational-total-war` (CTW). Treat CTW as a read-only dependency.
Do not copy work-in-progress analysis into the production source.

## Boundaries

- Verify `source_lock.json`, exact source commit and unmodified tracked source files.
- Reusable code belongs in `src/`; methodology and compact reviewed artifacts in `studies/`.
- Regenerable matrices, unit tables, caches and exploratory work belong under ignored `work/`.
- Never edit CTW `data/`; preserve stable database identifiers.
- Blank is not zero. Unit cards exclude technologies, skills, lord effects,
  difficulty, fatigue, terrain, temporary abilities and mods unless explicitly modeled.

## Race tactical possibility space

Read `studies/race_strategy_space/methodology.md`, then its `feature_schema.json`.

- `race_features.py`: source loading, unit scoring and capability aggregation.
- `janus_distance.py`: weighting, distances, signed contrasts, convex archetypes,
  feature perturbations, label alignment and local residuals.
- `build_race_strategy_space.py`: source validation and the seven-file output contract.

```bash
python -m ctw_analysis.build_race_strategy_space --ctw-root ../computational-total-war
python -m ctw_analysis.build_race_strategy_space --ctw-root ../computational-total-war --verify-regeneration
CTW_TEST_ROOT=../computational-total-war python -m unittest discover -s tests -v
```

Use one numerical-library thread for the recorded deterministic runtime.
Canonical view names are `breadth`, `ceiling`, `cost_access`.
The primary model has 54 dimensions. Unit tier is topology sensitivity only.
Interpret distances and signed contrasts first; archetypal memberships and local
residuals explain continuous relationships. Separate entropy from uncertainty.
Use total variation for membership movement; preserve and report pole movement.
Keep optimization repeatability, local robustness and structural stress separate.
Local perturbations preserve every dimension and equal block totals. Structural
stress does not gate selection. Without explicitly adopted membership/pole
tolerances, keep `selected_resolution` null with `tolerances_not_adopted`; this
status does not mean stability failed. Show the conditional tolerance grid and
mark the error-knee basis provisional. Preserve tail events and convergence flags. Do not assign semantic pole names before
inspecting the fitted coordinates. Do not infer causal tactics or played armies
from roster capability summaries.

When changing the schema, regenerate all seven reviewed outputs and rewrite the
superseded documentation. Exact artifact-set and byte regeneration are required.
