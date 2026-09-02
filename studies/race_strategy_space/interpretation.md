# Provisional interpretation

The feature pass supports **overlapping strategic neighborhoods**, not clean
race classes. The best tested hard partition uses seven labels, yet its
silhouette is only 0.0911. Several labels are therefore boundary cuts through a
continuous space, and two are single-race residues.

The consensus partition is:

| Label | Races |
|---|---|
| 0 | Bretonnia, Empire |
| 1 | Dwarfs |
| 2 | Beastmen, Kislev, Slaanesh, Wood Elves |
| 3 | Daemons of Chaos, Khorne, Lizardmen, Norsca, Nurgle, Tzeentch, Warriors of Chaos |
| 4 | Chaos Dwarfs, Dark Elves, Grand Cathay, High Elves, Ogre Kingdoms |
| 5 | Greenskins, Skaven, Tomb Kings, Vampire Coast |
| 6 | Vampire Counts |

These numeric labels carry no semantic meaning and should not be renamed as
archetypes without inspecting the feature profiles. In particular, a singleton
does not mean a race is incomparable; it means this forced partition did not
assign its local neighborhood the same boundary as another race.

The most defensible comparison object is therefore:

> standardized feature distance + perturbation co-clustering frequency

Use the nearest-neighbor entries in `clustering_report.json` to examine local
similarity, and use the 0–100 composites to explain *why* two races are near or
far. The composite scores are sample-relative capability summaries, not balance
or power rankings.

