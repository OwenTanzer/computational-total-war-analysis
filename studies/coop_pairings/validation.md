# Executed validation

MSI audit date: **2026-09-06**. Status: **pipeline checks passed with documented evidence gaps**. This is implementation validation on the PR branch, awaiting review and merge. It is not a live multiplayer playtest or proof of complete campaign-data coverage.

## Results

- Exactly **104** playable faction keys agree between the atlas and normalized faction index.
- Exactly **5,356** unique unordered pairs; every key occurs in **103** pair rows.
- **114** qualifiers: **33 Clean, 80 Workable, 1 Special**; **7 Immediate, 72 Regional, 35 Extended**.
- **237** nearby rejected pairs retain their geography and diplomatic reasons. This includes failed Extended geography gates, not just diplomatic conflicts.
- **29** zero-observed-partner factions: **18** have missing start/capital regions; **11** have resolved capitals but no partner satisfying the frozen envelope and diplomatic policy. These are not proven absolute zero-partner factions because missing-start pairs remain unresolved.
- **1,701** pair geographies are unresolved and explicitly excluded from qualification; every pair still has a diplomatic class and evidence/uncertainty fields.
- Source HEAD, snapshot, consumed working-file Git blobs, atlas integrity, and atlas/economy validation reports pass. All **24** faction guides pass the upstream structural validator; all local source evidence anchors resolve.
- A second independent generation produces byte-identical bytes for **all 14 generated study files** and the **6.7 MB** ignored all-pairs CSV. Generated artifacts use LF line endings on all platforms.
- **29 tests passed**, including **18 new pairing tests** and **11 existing strategy-space tests**. Integration tests ran against the actual locked atlas; none were skipped.
- `git diff --check` passes. The source dependency remains clean; the original MSI source checkout's unrelated edits remain untouched.

## Commands executed

```powershell
.venv/Scripts/python -m ctw_analysis.coop_pairings --ctw-root C:/Users/Owen/ctw-source-locked --verify-regeneration
$env:CTW_TEST_ROOT='C:/Users/Owen/ctw-source-locked'
.venv/Scripts/python -m unittest discover -s tests -v
```

From the locked source checkout:

```powershell
node scripts/faction-guide-queue.mjs validate-all
```

Runtime: Windows, Python **3.14.4**, Node **24.15.0**. The isolated environment installed declared project dependencies: NumPy **2.5.3**, pandas **2.3.3**, SciPy **1.18.1**, scikit-learn **1.9.0**. The pairing pipeline uses only the standard library. The initial system-Python test attempt could not import SciPy for the existing study; installing the repository's declared dependencies in `.venv` resolved this, without changing their declared version ranges.

The focused tests cover null geometry, disconnected paths, cross-theater maritime ambiguity, short-range same-theater raster holes, Extended boundary gates, unordered-pair duplicates, wrong source commits, actual atlas counts and Gaean Vale's absent adjacency, the stale Gorbad/Wurrzag row, incomplete-baseline accounting, deterministic bytes, Wulfhart's scoped teammate exception, Repanse/Arkhan modifiers, Azazel/Kemmler bridges, marked WoC rivalry, withheld Golgfag/Beastmen eligibility, shared rewards and Eshin friction, and single-player objectives not becoming multiplayer war locks.

## Remaining acceptance gaps

1. The locked atlas has 104 faction identities, but only **86 capital geometries**. Starting forces are explicitly unavailable. Scripted starts and relocations need authoritative upstream evidence.
2. Numeric aversion, opening treaties, all relevant faction/lord/technology effects, Beastmen permitted-faction membership, and Golgfag's team/alliance exception are not fully established. Guide-backed exceptions are preserved; generic policy remains analytical inference.
3. Strategic nodes and caravan/convoy links do not establish universally open player movement routes. Islands and portals retain explicit uncertainty.
4. The recovered Notion page has only one named pair, no regional enumeration, and none of the other **123 candidate identities**. Complete pair-level change/new-pair/underrepresentation analysis is unavailable.

For these reasons [coverage_report.json](coverage_report.json) sets `acceptance_complete=false` and `issue_closure_recommended=false`. No `Closes #6` claim is appropriate. Source validation also retains the atlas's unrelated warning about three engine-resolved battle-map groups without exposed direct mappings. Guide completion is structural and does not independently reproduce every documented game mechanic.
