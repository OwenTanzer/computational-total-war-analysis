# Executed validation

MSI audit date **2026-09-06**, patch **8.1.1**, build **24237342**. Implemented and validated on the PR branch; awaiting review and merge. Source-based validation does not claim runtime multiplayer playtesting.

- **104** faction keys agree across atlas and index; **5,356** unique unordered pairs; each faction occurs **103** times.
- All **104 primary starts resolve**; **zero unresolved geography pairs**. Four maritime points retain null region/path fields and explicit bounded land anchors.
- **146 qualifiers:** 30 Clean, 115 Workable, 1 Special; 10 Immediate, 85 Regional, 51 Extended. **354 nearby rejections** preserve reasons.
- **13 zero-partner factions** under the policy: Knights of Caledor, Harbinger of Disaster, Slaughterhorn Tribe, Ghosts of Pahuax, The Maneaters, High Elf Sea Patrol, The Tormentors, Shadow Legion, Ursun Revivalists, Oracles of Tzeentch, Warherd of the One-Eye, Warherd of the Shadowgave, World Walkers. This does not prove that all possible co-op modes/alliances are impossible; treaty uncertainty is explicit.
- Prior implementation comparison: **98 retained, 48 added, 16 removed; 20 retained proximity changes**. This compares real rows from analysis commit c169e19, not the incomplete Notion list.
- **31 analysis tests pass**, including 20 pairing tests and 11 existing strategy-space tests. Integration checks use the actual locked source; none skipped.
- **16 generated study files and the full all-pairs CSV regenerate byte-identically**. Source HEAD, snapshot, consumed Git blobs, SQLite integrity and source evidence anchors pass.
- Upstream source repair: **10 focused tests pass**; all **569 settlement controls** match; 104 primary generals/109 total generals/308 binary characters and five partner overrides validate. All 1,017 logical/world control pairs fit within 0.0001. Two base-to-enriched atlas builds are byte-identical; existing validation-text tests pass. The original atlas warning about three engine-resolved battle-map groups remains unrelated.
- Geographic freeze 400dfbd precedes intersection with diplomacy. No diplomatic rules were changed in the starting-position repair.

```powershell
.venv/Scripts/python -m ctw_analysis.coop_pairings --ctw-root C:/Users/Owen/ctw-startpos-repair --verify-regeneration
$env:CTW_TEST_ROOT='C:/Users/Owen/ctw-startpos-repair'
.venv/Scripts/python -m unittest discover -s tests -v
```

Source reproduction and exact validation commands are linked from [source PR #6](https://github.com/OwenTanzer/computational-total-war/pull/6). Tests cover maritime nulls versus known points, missing geometry, disconnected Gaean Vale, Extended gates, Gelt's recovered army, Khazrak partner branches, actual stale Gorbad/Wurrzag exclusion, uniqueness and coverage, source-lock failure, deterministic outputs and scoped diplomatic exceptions.

Remaining gaps: static startup/runtime adjustment uncertainty; incomplete generic diplomacy/modifiers and Beastmen/Golgfag eligibility; travel access; the 123 unrecovered historical pair identities. These remain visible in [coverage_report.json](coverage_report.json); acceptance is incomplete and issue #6 remains open. Original unrelated MSI source changes are preserved. Nothing is merged.
