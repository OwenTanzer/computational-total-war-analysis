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
- `build_race_strategy_space.py`: source validation and the ten-file output contract.

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
Local perturbations preserve every dimension and equal block totals. Keep all
K=3–8 representations; the knee is descriptive only. Never select a winning K.
Report tolerance comparisons for all K, full distributions and optimizer attempt
histories. Nearest-profile links across K allow many-to-one correspondence and
must not be described as proven ancestry or causal splitting.

- `capability_packages.py`: source-unit witnesses and exact one/two-unit frontiers.
- `assumption_sensitivity.py`: block emphasis and requirement-dependent cost comparisons.

Keep same-unit and distinct-provider capabilities separate. All-units speed means
minimum selected speed; do not average it. Never sum capability proxy scores into
army power. Preserve all minimum-cost ties on the published grid and exact-objective
frontier ties. Raw measurement missingness remains unavailable, not zero. Baseline
proxy formulas retain their inherited imputation and must be labeled as proxies.
Link units using race and stable unit keys. Package attainability means roster-listed
access, not faction recruitment legality, synergy or battle effectiveness.
Do not assign semantic pole names without unit and capability-profile evidence.

When changing the schema, regenerate all ten reviewed outputs and rewrite the
superseded documentation. Exact artifact-set and byte regeneration are required.
