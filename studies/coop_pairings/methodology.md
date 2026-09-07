# Immortal Empires two-player pairing audit

Issue: [#6](https://github.com/OwenTanzer/computational-total-war-analysis/issues/6). Audit date: **2026-09-06**. Scope: vanilla Immortal Empires, patch **8.1.1**, Steam build **24237342**, two independent human teammates. Implemented and validated on the pull-request branch; awaiting review and merge.

The pipeline enumerates every one of the **5,356 unordered pairs among 104 playable factions**. The frozen analytical policy produces **114 qualifiers** (33 Clean, 80 Workable, 1 Special), **237 nearby rejections**, and **29 factions with zero observed qualifying partners**. This is an exhaustive application of explicit rules to the available evidence, **not a claim that all 104 factions' actual starts or multiplayer diplomatic behavior have been verified**. Eighteen factions have no atlas capital/start region, leaving 1,701 pair geographies unresolved. Acceptance is therefore incomplete and issue #6 must remain open.

## Source lock and provenance

`source_lock.json` remains unchanged at CTW commit `8c2169b837288d03ba0188b468f06a2f3bcb4b28`. The MSI's original source checkout was newer and dirty. A separate checkout of the locked commit was created at `C:/Users/Owen/ctw-source-locked`; no original source file or local change was modified. The analysis lives at `C:/Users/Owen/ctw-analysis-issue6` on `feat/issue-6-coop-pairings`, based on analysis main `fb17eb88c3a5f9f5707245ecfea9fa36d65518f1`. Remote branches and PRs were checked before implementation; no issue-6 implementation existed (the prior scoring/access PR #4 was already closed).

Retrieval followed source `AGENTS.md`: catalog, dataset READMEs, economy manifest/schema/index and guide queue, narrow SQLite schema/queries, then source validation and applicable guide sections. Campaign atlas schema is embedded in SQLite rather than a standalone manifest; the consumed schema inventory is saved in [source_provenance.json](source_provenance.json). No economy building CSV, character CSV, full raw export or binary atlas is copied into this repository.

Every run checks HEAD against the lock, exact snapshot metadata, the presence and clean state of consumed inputs, and each working file's Git-filtered blob against its locked blob. It checks atlas and economy validation status, guide queue completion, atlas SQLite integrity, and every evidence anchor. Windows CRLF checkouts are handled through Git filters. Atlas SHA-256, input Git blob IDs, metadata, schema and source coverage are retained. SQLite opens with `mode=ro` and `query_only`; output paths inside the source dependency are rejected.

## Recovered Notion baseline

The existing page is [Immortal Empires Co-op Pairing Atlas — Patch 8.1.1](https://www.notion.so/3d33c519147b81d2b920e93cc2d8792b), under the user's games-library page `3773c519-147b-81a9-9fe6-cc080b7475a9`. Its September 6 creation, project location and exact count/audit-plan text identify it. The complete Markdown response was untruncated, with no unknown blocks or nested baseline pages.

[The preserved historical text](baseline_september_6.md) contains **124 pre-audit candidates**, **123 after a stale Gorbad + Wurrzag flag**, and the correction that the purported **61-pair shortlist contained 62**. It explains the 62 + 53 + 9 reconstruction. It contains **only the single named Gorbad + Wurrzag pair**, no full table, no 62-row shortlist, no 53 pruned rows, no nine added rows, no old class columns, and **no regional groupings**. Thus 123 candidate identities are unrecovered. These counts never control generation.

Only the one actual named row is resolved to stable faction keys and compared. Its earlier stale flag is corroborated: Black Crag to Cuexotl, 267.842831 logical units, eight raster borders, Distant/Clean, excluded. This is a changed inclusion status relative to its original candidacy, not discovery of a previously unknown correction. The other generated rows cannot be called newly discovered omissions; systematic underrepresentation and old classification changes cannot be measured. [Comparison detail](preliminary_vs_generated.md), [machine-readable comparison](baseline_comparison.json), and [recovered row](baseline_pair_comparison.csv) preserve these boundaries.

## Geographic layer and freeze

`coop_geography.py` accepts only the atlas connection. It has no diplomatic inputs. It sorts `faction_start_reference` by canonical key and uses its capital region, joining region metadata and the normalized economy index. The faction/index sets and culture/subculture identities must match exactly. Labels remain labels; no missing name is inferred from a similar key.

Distances are Euclidean distances between **region-mask centroids in the game's logical coordinates**. These are neither army coordinates nor settlement coordinates. The graph is the undirected raster-border graph of spatial, province-bearing regions. Province neighbors are induced by a border between their regions. Province-less Unknown Terrain and Chaos Wasteland cannot create giant shortcuts. Breadth-first search measures the fewest raster borders; absence of a path is null, never zero. There is no cost or movement-turn interpretation.

Theaters use **only** atlas `cai_region_hint_area_*` memberships. Shared groups are preserved; otherwise the pair is browsed under its two atlas areas. `unmapped` means no broad atlas area, not a remembered theater. No coordinates or regional labels were supplied from memory or web maps.

The 86 observed starts give 3,655 measured distances: approximately 47 at the first percentile, 69 at 2.5%, 96 at 5%, 135 at 10%, and 346 at the median. The 100/150 distance boundaries roughly bracket the lower 5–10% of the distribution; 75 is a conservative short-range, same-theater alternative near the lower 2.5%. These are analyst-selected proximity thresholds, not inferred movement limits. [calibration.json](calibration.json) records the full distribution summary.

Apply the following rules **in order**:

| Class | Rule | Geographic qualification |
|---|---|---|
| Unresolved | Either centroid unavailable | Withheld; not Distant |
| Immediate | Same non-null province, or at most one raster border **and** distance ≤100 | Yes |
| Regional | Distance ≤100 **and** (neighboring provinces **or** at most four raster borders) | Yes |
| Extended | Distance ≤150 **and** (shared broad atlas theater **or** neighboring provinces **or** at most six raster borders), after the earlier rules fail | Only if a shared broad theater exists **and** (at most six raster borders **or** distance ≤75) |
| Distant | Otherwise | No |

V1 was frozen in `406113f` before generating diplomacy. A subsequent topology QA query found that **Gaean Vale has a centroid but zero adjacency records**, so a mandatory path excluded nearby same-theater starts. The distance ≤75 same-theater alternative was independently added and refrozen in `ce3e05a`; final diplomacy was then regenerated. It applies to every pair, with no faction whitelist or target pair count. This correction is disclosed rather than pretending the initial freeze was final. Sanity cases include Gaean Vale/Lothern (about 51 units, no path, Extended); Lothern/Tor Yvresse (about 71 units, seven borders, Extended); Reikland/Wissenland (about 31 units, two borders, Regional); and Black Crag/Cuexotl (about 268 units, eight borders, Distant).

**Maritime, islands and strategic links:** all 119 stored links are caravan/convoy route segments, not ordinary player-army routes. Their stable network keys are joined to endpoint regions and retained per pair as context. There are 261 teleportation nodes among 372 strategic nodes; Belakor, Changeling, endgame, faction-unlocked and sea-lane networks have different eligibility. The atlas supplies no validated general traversal edges or player-access state for them. Node coordinate fields from different source tables are not assumed interchangeable for new route distances. No portal or trade route shortens the graph. Islands and disconnected masks can qualify through the short-range/shared-theater rule, but still carry null path and an explicit disconnected flag. Cross-theater sea pairs without supporting topology do not qualify under this conservative envelope, which is a scope limitation, not proof that sailing is impossible. Aislinn's zero-time sea lanes, Lokhir's unlocks, Worldroots and other scripted travel are guide caveats rather than fabricated start positions or universally open routes.

## Independent diplomatic policy

`coop_diplomacy.py` receives faction keys/races and scoped single-player objective pointers; it receives **no coordinates, theater or proximity class**. [race_policy.json](race_policy.json) expands every unordered race prior, including within-race cases. [faction_evidence.csv](faction_evidence.csv) covers every faction and [evidence_registry.json](evidence_registry.json) resolves rules to exact locked guide paths, source-line anchors and scoped paraphrases.

The four classes describe **analytical compatibility of surrounding diplomatic ecosystems**, not engine treaty legality:

- **Clean:** a compatible ecosystem prior with no modeled structural friction; still subject to the explicit missing numeric-aversion evidence.
- **Workable:** sustainable coordination is inferred despite meaningful friction, competing progression or a conditional relationship bridge.
- **Special:** an explicit teammate exception or unusual treaty mechanism needs a caveat. If eligibility remains unproved, `treaty_eligibility_unresolved=true` withholds qualification even though the class is Special.
- **Conflict:** evidence plus the ecosystem policy indicates structural opposition. This does not claim the engine forbids putting those humans on a team.

Same-race, human/Order, Chaos and undead priors are only the starting layer. Wood Elf/Lizardmen territorial systems and Dwarf–High Elf friction make those Order combinations Workable. Rival-god priors extend to the exact marked WoC factions. Cross-ecosystem Conflict and pragmatic non-Order/mercenary Workable judgments are explicitly **inferences**: the locked inputs do not contain an exhaustive generic numeric aversion matrix, opening wars/treaties, or all lord/faction/technology modifiers. They are not disguised as measured relationship values. Faction-specific evidence changes or qualifies these priors:

- Wulfhart–Lizardmen uses the documented teammate exception (Special); Repanse's −80 undead relations produce Conflict.
- Arkhan has −60 Tomb King/+40 Vampiric Undead relations. He is Conflict with ordinary Tomb Kings, Clean with vampires, and uses an explicitly inferred opposed living/undead prior for Order partners.
- Azazel's +80 human-race bonus supports Workable rather than blanket Order/Chaos Conflict; Kemmler's +30 bridge is limited to WoC/Beastmen/Norsca; Malus's daemon bonus is conditional on possession.
- Beastmen's permitted-faction membership is not listed by the guide. Their restricted treaty set does not prove an allowed teammate alliance; qualification is withheld. Golgfag's alliance ban and team-aware contracts similarly do not prove a lobby override.
- Nakai's locked Defenders vassal, Settra's no-vassal rule, N'Kari's exclusion of humans from forced seduction, WoC's specific homeland/final-settlement routes, and human exclusions in defeat/Cult confederation are not generalized into automatic absorption or compulsory human vassalage.
- Eshin's clan-contract diplomacy, Chaos Dwarf seat competition, shared multiplayer Books of Nagash, and global Wood Elf rites/Ariel prevent unqualified same-race Clean claims. Sayl's inert Confidence-war listener is not reported as operative. Epidemius's Tally does not protect non-Nurgle allies from negative plagues.
- Har Ganeth's Blood Voyage targets and Khalida's permanent no-peace with the nonplayable Lahmian Sisterhood remain precisely scoped. A lock on a scripted/nonplayable faction is not a lock on every playable race member.

Partner-targeted atlas **single-player** objectives are preserved with objective key/type and can downgrade Clean to Workable. They do not automatically become multiplayer forced wars. Wulfhart's explicit teammate exception remains Special even with an Itza objective. Co-op may therefore require foregoing competing personal objectives; the study does not promise simultaneous completion of every personal mission.

## Intersection, outputs and validation

`included = geographic_envelope AND diplomatic_class != Conflict AND NOT treaty_eligibility_unresolved`. All pair rows, including distant and unresolved rows, remain reproducible in ignored `work/coop_pairings/all_pairs.csv`. CSV blank numeric/start fields mean unavailable. Booleans serialize as `True`/`False`. Evidence IDs join on semicolons to the JSON registry; all identifiers are stable game keys. No inferred numeric modifier is stored.

Committed outputs:

| Artifact | Purpose |
|---|---|
| [qualifying_pairs__8.1.1.csv](qualifying_pairs__8.1.1.csv) | Every qualifier, metrics, both classes, keys, source facts, inferences, caveats |
| [regional_pairings.md](regional_pairings.md), [regional_summary.csv](regional_summary.csv) | Complete regional enumeration and compact totals |
| [nearby_rejected.csv](nearby_rejected.csv) | All rejected Immediate/Regional/Extended pairs, including failed Extended gates |
| [faction_coverage.csv](faction_coverage.csv), [coverage_report.json](coverage_report.json) | Every faction's qualifying count including zero, unresolved counts, validation and gaps |
| [preliminary_vs_generated.md](preliminary_vs_generated.md), baseline CSV/JSON | Honest one-row comparison and missing-baseline accounting |
| [source_provenance.json](source_provenance.json), [evidence_registry.json](evidence_registry.json), [faction_evidence.csv](faction_evidence.csv) | Locked sources and scoped diplomatic evidence |
| [output_hashes.json](output_hashes.json) | SHA-256 of generated study outputs |
| [validation.md](validation.md) | Executed checks and practical limits |

## Reproduction on this MSI

From `C:/Users/Owen/ctw-analysis-issue6`, after `python -m venv .venv` and `.venv/Scripts/python -m pip install -e .`:

```powershell
.venv/Scripts/python -m ctw_analysis.coop_pairings --ctw-root C:/Users/Owen/ctw-source-locked --verify-regeneration
$env:CTW_TEST_ROOT='C:/Users/Owen/ctw-source-locked'
.venv/Scripts/python -m unittest discover -s tests -v
```

Portable equivalent: `python -m ctw_analysis.coop_pairings --ctw-root ../computational-total-war --verify-regeneration`. The pairing module itself uses only the standard library; with an uninstalled checkout set `PYTHONPATH=src`. `--output` and `--work-dir` support separate review destinations. Missing or mismatched sources fail, rather than silently updating the lock.

## What remains to satisfy the full issue

Recover authoritative human campaign starts for the 18 missing factions and audit scenario-script relocations; establish portal/sea-lane traversal eligibility if expanding the envelope; export/reconcile generic diplomatic modifiers and unresolved treaty/team rules; and recover the 123 missing historical pair identities plus old region/class columns. Any upstream snapshot change requires a separately reviewable `source_lock.json` update and fresh calibration. The current source guide validator is structural, not a multiplayer simulation. The pipeline and its reproducibility are validated; those evidence gaps remain open.
