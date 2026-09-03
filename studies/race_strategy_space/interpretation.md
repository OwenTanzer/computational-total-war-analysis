# Provisional interpretation

The corrected feature pass still supports **overlapping strategic
neighborhoods**, not clean race classes. Structural zeros now remain zero,
ordinary non-explosive missile units no longer receive bombardment credit, and
campaign unit-tier access complements multiplayer-cost access.

The best tested hard partition now uses eight labels, with a silhouette of
0.1226. This is stronger than the original 0.0911 result but still weak evidence
for natural, sharply separated classes. Several labels remain boundary cuts
through a continuous space, and two remain single-race residues.

The new consensus partition is:

| Label | Races |
|---|---|
| 0 | Bretonnia, Empire |
| 1 | Dwarfs |
| 2 | Chaos Dwarfs, High Elves, Ogre Kingdoms |
| 3 | Dark Elves, Grand Cathay, Greenskins, Skaven, Tomb Kings, Vampire Coast |
| 4 | Beastmen, Kislev, Slaanesh, Wood Elves |
| 5 | Khorne, Nurgle, Tzeentch |
| 6 | Daemons of Chaos, Lizardmen, Norsca, Warriors of Chaos |
| 7 | Vampire Counts |

These numeric labels carry no semantic meaning and should not be renamed as
archetypes without inspecting the feature profiles. In particular, a singleton
does not mean a race is incomparable; it means this forced partition did not
assign its local neighborhood the same boundary as another race.

## Sensitivity to campaign access

The cost-only sensitivity run also selects eight clusters, with a silhouette of
0.1203. Its principal structural difference is that Dark Elves remain with
Chaos Dwarfs, High Elves, and Ogre Kingdoms, while Grand Cathay joins
Greenskins, Skaven, Tomb Kings, and Vampire Coast. Adding unit-tier access moves
Dark Elves into that latter neighborhood and leaves Grand Cathay there.

Greenskins therefore remain beside Skaven, Tomb Kings, and Vampire Coast after
the normalization and bombardment corrections. Their local neighborhood also
becomes more stable: Dark Elves are now their nearest race at distance 0.885,
followed by Skaven at 1.035, with perturbation co-clustering frequencies of
0.654 and 0.550 respectively. Their bombardment composite rises from seventh to
fifth because removing phantom archer credit sharpens the contrast between
genuine cheap artillery and merely possessing ranged units. Missile pressure,
by contrast, falls from fourteenth to sixteenth once campaign access is
included.

The most defensible comparison object remains:

> standardized feature distance + perturbation co-clustering frequency

Use the nearest-neighbor entries in `clustering_report.json` to examine local
similarity, and use the 0–100 composites to explain *why* two races are near or
far. The composite scores are sample-relative capability summaries, not balance
or power rankings.
