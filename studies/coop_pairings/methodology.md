# Immortal Empires two-player pairing audit

Issue: [#6](https://github.com/OwenTanzer/computational-total-war-analysis/issues/6). Audit date: **2026-09-06** (MSI local date). Scope: vanilla Immortal Empires, patch **8.1.1**, Steam build **24237342**, two independent human teammates. **Implemented and validated on the pull-request branch; awaiting review and merge.**

All **5,356 unordered pairs among 104 playable factions** are evaluated. The repaired source resolves every primary army position, including the 18 factions without atlas capitals. The frozen policy produces **146 qualifiers: 30 Clean, 115 Workable, 1 Special**; **10 Immediate, 85 Regional, 51 Extended**. There are **354 nearby rejections**, **13 zero-partner factions**, and **zero unresolved pair geographies**. These are analytical compatibility results backed by static source evidence, not 5,356 multiplayer playtests. Diplomatic and historical-baseline gaps still prevent closing issue #6.

## Source repair and explicit lock update

The original lock was `8c2169b837288d03ba0188b468f06a2f3bcb4b28`. After the user authorized repairing the missing starts, a separate source branch was created at `C:/Users/Owen/ctw-startpos-repair`, based on source main `5d25716de3d18d0006f95d7aa623a7c062d72834`. Source [PR #6](https://github.com/OwenTanzer/computational-total-war/pull/6) adds validated army-start evidence. This analysis explicitly locks its unmerged commit **91b019866c7fd3afe72063cd0c4d7a9fd3830124**. The intervening main history includes the merged technology work; the patch/build stay unchanged. Review the lock bump together with that upstream PR. The original MSI checkout's unrelated changes remain untouched.

The analysis branch is `feat/issue-6-coop-pairings` at `C:/Users/Owen/ctw-analysis-issue6`. Existing branches and PRs were checked before work; this follow-up updates the existing [analysis PR #7](https://github.com/OwenTanzer/computational-total-war-analysis/pull/7). Nothing is merged. Source candidate production files were promoted only inside the isolated source branch after validation. The analysis treats that checkout as read-only.

Retrieval follows source `AGENTS.md`: catalog, relevant README, manifest/schema, faction index, narrow SQLite queries, guide evidence, and validation. The new `faction_army_start_reference` comes from the installed compressed ABCB `startpos.esf`, matched to stable faction/frontend-leader subtype keys. It has **104 primary generals**, with **109 generals** including secondary forces and **308 binary characters** retained upstream. All **569 land settlement controls** match their own atlas raster masks. Stored world coordinates and script logical coordinates are distinct: the hex-grid transform is checked against all **1,017 binary character points**, with maximum residual below 0.0001. Only script targets use the fitted transform.

Human custom starts are evaluated statically in source order. Eltharion and Orion relocate; five partner-specific rows preserve Khazrak's human/AI predicate. AI-only Aislinn, Wulfrik and Daemon Prince moves do not overwrite human starts. Later Gelt/Ostankya/Teclis choices are excluded. Secondary forces remain available upstream but do not set the primary distance. This is not a post-script hero census or verification of engine teleport adjustment. The existing capital view remains intact.

Each run verifies HEAD, snapshot, clean consumed inputs and their Git-filtered blob hashes, atlas integrity, source validation status, faction/index identity agreement and diplomatic evidence anchors. SQLite uses `mode=ro` and `query_only`; outputs inside the dependency are rejected. [source_provenance.json](source_provenance.json) records the lock, hashes, actual SQLite schema, validation and source PR.

## Historical Notion baseline

The existing [Immortal Empires Co-op Pairing Atlas — Patch 8.1.1](https://www.notion.so/3d33c519147b81d2b920e93cc2d8792b) was identified by its September 6 content and games-library parent `3773c519-147b-81a9-9fe6-cc080b7475a9`. The untruncated original text is preserved in [baseline_september_6.md](baseline_september_6.md) and as a clearly labeled historical section on the same live page.

It reports **124 candidates**, **123 after flagging Gorbad + Wurrzag**, and corrects the “61-pair” shortlist to **62** (62 + 53 + 9 reconstruction). It contains only **one named pair**, no full regional enumeration, no old classifications and none of the other **123 candidate identities**. Counts never constrain regeneration. A complete baseline-level comparison, newly discovered omissions or systematic underrepresentation cannot be claimed.

The actual named row remains excluded: Gorbad's army is in **Iron Rock**, Wurrzag's in **Sun Tree Glades**, **233.832041 world units** apart and nine raster borders, **Distant / Clean**. The prior capital proxy was Black Crag/Cuexotl at 267.842831 units; the repaired start-region centroids are 237.371859 units apart. Both substantiate the historical stale-inclusion flag. See [preliminary_vs_generated.md](preliminary_vs_generated.md).

The prior *implemented* 114-qualifier result is a separate, complete comparison target: analysis commit `c169e19f154784759041677d1def85dd5844c946`. [prior_capital_proxy_qualifiers.csv](prior_capital_proxy_qualifiers.csv) preserves its actual compact rows. The repair **retains 98, adds 48 and removes 16** qualifiers; **20 retained pairs change proximity class**. These are changes relative to the earlier implementation, not claims about the missing Notion rows. [start_repair_comparison.csv](start_repair_comparison.csv) records every row in the union, and [start_region_corrections.csv](start_region_corrections.csv) audits all 104 old capital proxies against army starts.

## Geography and independent freeze

`coop_geography.py` consumes only the atlas; diplomacy receives no geography. `geographic_distance` is Euclidean distance between primary human army **world coordinates**. `centroid_distance` separately measures start-region mask centroids when both exist; it is blank for maritime starts. World coordinates are not script hex coordinates, campaign turns, or path costs. Old code used capital centroids for distance; this correction changes the measurement rather than disguising those proxies as actual starts.

The graph is the atlas's undirected raster-border graph of 569 spatial, province-bearing regions and 1,293 edges. It excludes province-less Unknown Terrain/Chaos Wasteland shortcuts. Province neighbors come from borders. Theaters use only `cai_region_hint_area_*` memberships. No geography comes from remembered starts or web maps.

Four primary human points have no distinct sea mask: **Noctilus, Eltharion, Aislinn and Wulfrik**. Their nearest uniquely colored land-mask cell is explicitly a descriptive anchor, not a claimed maritime region or landing route. All four gaps are below 12 world units; the frozen policy permits such anchors only up to **25**. `start_region_*` and `raster_hops` remain blank for a maritime pair. `land_anchor_*`, `land_anchor_hops`, `maritime_anchor_inference` and the gap columns expose the inference. Anchor-based theater/province relationships support regional browsing and proximity, not sailing feasibility. Maritime pairs can never be Immediate.

Rules are applied in order, with distance referring to army-point world distance:

| Class | Rule | Qualifies geographically |
|---|---|---|
| Unresolved | A primary world point is missing | No; zero such cases in this snapshot |
| Immediate | Both starts are land, same non-null province; or at most one border and distance ≤100 | Yes |
| Regional | Distance ≤100 and neighboring provinces or at most four borders | Yes; maritime versions use bounded coastal anchors and downgrade an otherwise Immediate result to Regional |
| Extended | Distance ≤150 and shared atlas theater, neighboring provinces or at most six borders, after earlier rules fail | **Only** shared theater AND (at most six borders OR distance ≤75); maritime anchors must also be ≤25 from the point |
| Distant | Otherwise | No |

For maritime pairs the relationship and border inputs in this table refer to explicitly labeled land anchors. Missing land paths are null, never zero. Islands/disconnected regions can qualify through the same-theater ≤75 alternative. `neighboring_province` is anchor-based when `maritime_anchor_inference=True`.

The revised geography was committed in **400dfbd before diplomatic intersection**. Thresholds 100/150/75 were retained; the measurement and bounded maritime handling were refrozen explicitly. The 5,356-point-distance quantiles are about 49 (1%), 71 (2.5%), 96 (5%), 137 (10%) and 354 (median). [calibration.json](calibration.json) freezes the complete calibration. No target count or diplomatic outcome determines the rules. Earlier freezes `406113f`/`ce3e05a` remain historical; the latter introduced the disconnected Gaean Vale safeguard.

All 119 atlas strategic links are caravan/convoy context, not ordinary army edges. The 261 teleportation nodes among 372 strategic nodes do not establish general player access. The new script audit confirms Belakor opens three nodes at startup; that is not an automatic relocation or universal teammate travel link. No portal, sea lane, Worldroots or trade route shortens the measured graph. These are conservative boundaries, not proof that travel is impossible.

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

## Outputs and reproduction

`included = geographic_envelope AND diplomatic_class != Conflict AND NOT treaty_eligibility_unresolved`. All 5,356 rows regenerate under ignored `work/coop_pairings/all_pairs.csv`. Missing fields are blank, never zero; flags serialize as `True`/`False`. Evidence IDs resolve to the JSON registry. No missing numeric aversion is fabricated.

Compact outputs under this directory include the qualifying CSV, complete [regional enumeration](regional_pairings.md), [nearby rejected appendix](nearby_rejected.csv), [all-faction coverage](faction_coverage.csv), historical comparison, starting-region and prior-implementation comparisons, evidence registry and [validation](validation.md). Sixteen generated files and the full ignored pair table are checked for byte-identical regeneration. [output_hashes.json](output_hashes.json) records their hashes.

From `C:/Users/Owen/ctw-analysis-issue6`:

```powershell
.venv/Scripts/python -m ctw_analysis.coop_pairings --ctw-root C:/Users/Owen/ctw-startpos-repair --verify-regeneration
$env:CTW_TEST_ROOT='C:/Users/Owen/ctw-startpos-repair'
.venv/Scripts/python -m unittest discover -s tests -v
```

Portable form: `python -m ctw_analysis.coop_pairings --ctw-root PATH --verify-regeneration`, with PATH checked out at the exact locked source commit. The pairing module uses only the standard library. The MSI venv includes the project's declared dependencies for the existing strategy-space tests. `--output` and `--work-dir` allow separate destinations. Lock mismatches fail rather than silently updating sources.

## Remaining acceptance gaps

The missing-primary-start problem is repaired, with static script and maritime qualifications. Numeric aversion, opening treaties, complete faction/lord/technology modifiers, Beastmen's permitted-faction membership and Golgfag's team/alliance exception are still incomplete. Portal/sea-lane access and runtime teleports are not playtested. The 123 missing historical candidate identities remain unavailable. Thus `acceptance_complete=false`, `issue_closure_recommended=false`; no `Closes #6` claim is appropriate.
