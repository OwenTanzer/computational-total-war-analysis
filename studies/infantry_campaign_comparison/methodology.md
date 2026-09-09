# Infantry campaign stat comparison

## Question and delivered scope

Does the displayed Iron Claw Tiger Warrior card establish the highest-stat
doomstack? This first pass screens the entire base unit dataset and reconstructs
explicit **partial** skill/technology modifier ledgers for five named army/unit
pairings. It does **not** identify a maximum attainable campaign card, simulate
battles, or claim an optimal army. Missing effects are unknown, not zero.

The target army form is one lord plus 19 identical units. The numerical block
totals cover the **19 units only**, excluding the lord's own health/damage.
Support-hero optimization is outside this pass. Sources are pinned by this
directory's `source_lock.json`; the repository-root lock remains unchanged for
the older race study, whose dependency lacks the completed technology dataset.

## Reproduce

With the source checkout at the exact study-local commit:

```bash
python src/ctw_analysis/infantry_campaign_comparison.py --ctw-root ../computational-total-war
python -m unittest discover -s tests -p 'test_infantry_campaign_comparison.py'
```

The runner verifies source commit, clean data working tree, snapshot, and the
three upstream audit statuses. It records SHA-256 hashes of inputs actually read.
Regenerable detailed tables live under ignored `work/infantry_campaign_comparison/`.
Compact outputs live under this study's `results/8.1.1/`.

## Base screen

Read all 24 normalized race files, deduplicate by stable unit key, and reject
cross-roster discrepancies in the compared stats. Select canonical
`tactical_category=infantry`, melee-infantry role, no missile weapon, small target
size, encyclopedia-visible, non-renown units. The role and size filters are
explicit additional restrictions, not replacements for the canonical category.
The source ontology can include unusual bodies such as Plague Toads in this
slice; we do not silently recategorize them. Monster, cavalry, artillery, hero,
and ranged doomstacks are not ranked by this study.

Use the raw `main_units.campaign_cap` to reject nonnegative caps below 19; -1 is
the source sentinel retained as the no-static-cap case. This is **not sufficient
to prove campaign acquisition of 19 copies**: Blessed units, Grudge Settlers,
recruitment pools, and dynamically expanded faction caps still need auditing.
Distinct unit keys sharing an English name remain distinct candidates. Rankings
are over records, not display names. Ties use competition ranking.

For N models, normal damage D, armour-piercing damage A, interval T, and an
assumed simultaneously attacking fraction f:

* Raw attack-capacity proxy = N × f × (D + A) / T.
* Armour-piercing attack-capacity proxy = N × f × A / T.
* Health of the 19-unit block = 19 × unit health.

Armour-piercing damage is already included in total damage. These are nominal
attack-capacity proxies, **not damage per second observed in battle**. They omit
hit probability, armour reduction, animations, target allocation, splash damage,
overkill, attack disruption, charge decay, fatigue, resistances of the target,
and contact effects. Splash target count must not simply multiply weapon damage.
Engagement sensitivities use f = 0.25, 0.5, 0.75, 1. Identical f for every unit
only rescales these proxies; it cannot predict the engagement geometry of a duel.
Large-target and infantry bonuses are separate axes rather than baked into a
fictional universal opponent. Speed remains in **source units**; its conversion
to the displayed card is not established by this analysis.

The base Pareto screen includes health, armour, attack, defence, speed, raw and
armour-piercing capacity, physical/missile/spell resistance, ward save, shield
block, barrier, charge, and target-size bonuses. A unit dominates another only
if it is at least equal on all axes and strictly better on one. Many dimensions
produce a large frontier. Being on it is not an elite-tier certificate, and base
dominance never eliminates a candidate from future campaign-bonus research.
No weighted grand total is produced.

## Reviewed campaign ledger

`profiles.json` explicitly selects source records for:

* Bhashiva / Iron Claw Tiger Warriors.
* Thorgrim / Hammerers.
* Grimgor / Black Orcs.
* Sigvald / Chosen of Slaanesh (Hellscourges).
* Festus / Chosen of Nurgle (Great Weapons).

Each record stores its exact source key, expected text, value, stat operation,
rank threshold, and condition. The program verifies the record against the
pinned source and rejects non-army effect scopes. These are **reviewed mappings
from explicit English descriptions**, not recovered effect-to-unit-set engine
joins. Ambiguous categories are excluded: for example, Hammerers are not assumed
to receive the technology labeled Great Weapon Infantry, and Tiger Warriors are
not assumed to be Yang units. All nonselected effect rows are retained in the
ignored unapplied-effects table for further audit.

Only the selected terminal skill-level row is used; ranks 1, 2, and 3 are not
summed. A conservative structural witness buys all prerequisite ancestors to
their maximum level, checks selected skill locks, and stays within a declared
49-point budget. This is a compatibility check, not an optimal allocation or
proof of campaign acquisition. Effects of prerequisite skills that were not
reviewed remain excluded. The profiles each have one source node-set variant.
Technology selectors likewise require one active variant and retain structural
conditions for inspection; building, resource, research-order and scripted
feasibility are **not fully solved**. Upstream topology/classification/script
audits are part of the evidence reviewed, not a substitute for that simulation.

Four explicitly separate conditions are calculated: rank-0 neutral, rank-9
neutral, rank-9 attacking in an ambush against Warriors of Chaos, and rank-9
defending a siege against Warriors of Chaos. The model rejects simultaneous
attacking and defending. Rank-9 states include supported per-rank and veteran
effects but **exclude native experience stat gains**, whose tables are absent.
They must therefore be called known-modifier subtotals, never complete cards.
The enemy-specific ledger is partial, including the relevant reviewed Bhashiva
and Thorgrim modifiers; it is not a claim of exhaustive opponent-specific effects.

Flat modifiers sum, and percentages sum within each stat. Two arithmetic
sensitivities are evaluated: percentage after flats, or percentage before flats.
For Grimgor's added armour-piercing damage this yields different results. The
reported min/max is only the span of those two conventions, **not certified
engine bounds**. No UI rounding, scalar caps, or hidden modifier channels are
invented. Resistance values are listed independently; no effective-health claim
is made by adding unlike resistance types.

## Screenshot and unresolved ceilings

No user screenshot values are distributed in this public study. The runner can
accept an optional `screenshot_observation` object in a private local copy of the
profiles configuration for residual analysis, but the published configuration
and outputs use repository-derived information only. Such a diagnostic does not
identify the depicted buffs, unit rank, or active conditions. Displayed speed
must not be compared without a verified source-to-card conversion.

The raw phase records named `ferocious_ambush` and `white_tiger` are retained
separately, including the former's 20-second duration and scalar modifiers.
Their names are useful evidence leads. Without the missing activation/phase
junctions and targeting relations, they are not inserted into a sustainable or
burst stack. No peak-burst maximum is published.

Global ceilings remain blocked by missing effect-operation/target junctions,
native rank scaling, complete item/trait acquisition and compatibility, abilities
and auras, faction rituals and unit upgrades, dynamic caps and repeatable bonus
rules. The result is a reproducible comparison of what is currently resolvable,
plus an explicit statement of what is needed to finish the campaign optimizer.
