# Provisional interpretation

The corrected feature pass still supports **overlapping strategic
neighborhoods**, not clean race classes. Structural zeros now remain zero,
ordinary non-explosive missile units no longer receive bombardment credit, and
the primary model retains multiplayer-cost access without pretending unit tier
is a campaign recruitment gate.

The best tested hard partition now uses eight labels, with a silhouette of
0.1203. This is stronger than the original 0.0911 result but still weak evidence
for natural, sharply separated classes. Several labels remain boundary cuts
through a continuous space, and two remain single-race residues.

The new consensus partition is:

| Label | Races |
|---|---|
| 0 | Beastmen, Kislev, Slaanesh, Wood Elves |
| 1 | Khorne, Nurgle, Tzeentch |
| 2 | Daemons of Chaos, Lizardmen, Norsca, Warriors of Chaos |
| 3 | Chaos Dwarfs, Dark Elves, High Elves, Ogre Kingdoms |
| 4 | Grand Cathay, Greenskins, Skaven, Tomb Kings, Vampire Coast |
| 5 | Vampire Counts |
| 6 | Bretonnia, Empire |
| 7 | Dwarfs |

These numeric labels carry no semantic meaning and should not be renamed as
archetypes without inspecting the feature profiles. In particular, a singleton
does not mean a race is incomparable; it means this forced partition did not
assign its local neighborhood the same boundary as another race.

## Unit-tier sensitivity

The non-primary unit-tier sensitivity selects eight clusters with a silhouette
of 0.1226. It moves Dark Elves from the Chaos Dwarfs–High Elves–Ogre Kingdoms
group into the Grand Cathay–Greenskins–Skaven–Tomb Kings–Vampire Coast group.
Because `main_units.tier` does not encode recruitment access, this movement is a
sensitivity to unit classification, not evidence about when commanders acquire
their options.

In the primary result, Greenskins remain beside Grand Cathay, Skaven, Tomb
Kings, and Vampire Coast after the normalization and bombardment corrections.
Dark Elves are their nearest race at distance 0.908, followed by Norsca at
1.040 and Skaven at 1.043. Their bombardment composite rises from seventh to
fifth because removing phantom archer credit sharpens the contrast between
genuine cheap artillery and merely possessing ranged units. Missile pressure
remains fourteenth, though its relative composite falls from 78.15 to 64.51.

The most defensible comparison object remains:

> standardized feature distance + perturbation co-clustering frequency

Use the nearest-neighbor entries in `clustering_report.json` to examine local
similarity, and use the 0–100 composites to explain *why* two races are near or
far. The composite scores are sample-relative capability summaries, not balance
or power rankings.
