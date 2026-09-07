## Preliminary count
**Working candidate total: 124 co-op pairings before systematic repository audit.**
Breakdown from the current hand-curated reconstruction:
- 62 entries in the old "final shortlist" (despite it having been described as 61)
- 53 regionally viable pairs that had appeared in the broader regional enumeration but were later pruned from that shortlist
- 9 additional candidate edges identified afterward as genuine or likely omissions
**Known stale item already flagged:** Gorbad + Wurrzag no longer satisfies the old regional assumption under the patch 8.1.1 map. Removing that one yields a provisional **123 surviving candidates**, but this is not yet the authoritative count.
<callout icon="⚠️" color="yellow_bg">
	Treat 124 as the pre-audit candidate count and 123 as the current post-flag working count. Neither is final until every playable faction pair has been regenerated from the repository data rather than inherited from the old hand-built list.
</callout>
## Audit plan against Computational Total War
1. **Lock the source snapshot.** Use only the Computational Total War patch 8.1.1 dataset as the primary source: 104 playable Immortal Empires factions, the campaign GeoPackage, and the completed faction guides. Use Computational Total War Analysis only for derived calculations and output artifacts.
2. **Generate the full pair universe.** Enumerate all `104 choose 2 = 5,356` unordered playable-faction pairs. The old shortlist becomes comparison data, not the search space.
3. **Compute start-position proximity from the campaign atlas.** Pull each playable faction's turn-one capital/start region from `faction_start_reference`; join to `region_points`, `regions`, `provinces`, `region_adjacency`, `strategic_nodes`, and `strategic_links`. For each pair compute direct logical-coordinate distance where available, province relationship, shortest region-adjacency path where meaningful, and explicit route/island handling for starts that are not represented cleanly by land adjacency.
4. **Classify geography rather than use one arbitrary radius.** Assign each pair to `Immediate`, `Regional`, `Extended`, or `Distant`. Calibrate the thresholds against the actual distance/topology distribution and obvious shared-theater examples, then freeze the rule before looking at diplomatic fit. Pairs outside the agreed proximity envelope are excluded from the viable set but retained in the audit table with their reason.
5. **Build diplomatic compatibility from repository faction information.** Use race/subculture identity as the baseline and the race faction guides for explicit diplomacy restrictions, exceptions, bespoke hostility, confederation/relationship rules, vassalization behavior, and multiplayer exceptions. Preserve special cases instead of forcing everything into Order/Chaos shorthand.
6. **Score diplomatic fit independently of geography.** Use `Clean`, `Workable`, `Special`, or `Conflict`. `Clean` means the alliance does not structurally sabotage either player's ordinary diplomatic ecosystem; `Workable` means manageable friction; `Special` covers multiplayer exceptions or unusual campaign mechanics; `Conflict` means the pair is fundamentally at odds and should not enter the recommended set.
7. **Intersect the two axes.** The exhaustive co-op list is every pair that is geographically `Immediate/Regional` (plus explicitly retained `Extended` cases) and diplomatically `Clean/Workable/Special`, with the exact reason for inclusion recorded.
8. **Run coverage and omission tests.** Every one of the 104 playable factions must either appear in at least one surviving pairing or be explicitly listed as having no qualifying local diplomatic partner. Compare the regenerated result against the 124 pre-audit candidates to identify false positives, stale pairs, and missed edges.
9. **Publish the audited artifact.** Replace this preliminary count with the final total and add the exhaustive pair table organized by theater, with proximity class, diplomatic class, evidence note, and source keys. Keep rejected-but-nearby pairs in a separate appendix so future map patches can be re-audited cleanly.
## Repository evidence currently established
- Campaign atlas: patch 8.1.1 / Steam build 24237342; 641 regions, 214 provinces, all 104 playable faction starts, region centroids/topology, and strategic links.
- Campaign atlas validation: passed with no errors.
- Faction guides: 24 playable-race guides covering all 104 playable factions.
This page is intentionally preliminary: it preserves the current count and the exact method we will use to replace hand-curation with a reproducible repository-grounded audit.
