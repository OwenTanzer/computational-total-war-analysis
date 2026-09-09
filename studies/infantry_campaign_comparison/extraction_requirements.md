# Evidence needed for a campaign ceiling

The first comparison is executable with the pinned repository alone. Extending
it to a ceiling requires the following source relations to be extracted and
normalized, with the same patch/build verification as existing CTW datasets.
This document is a bounded specification, not a request to change production
data by hand or infer missing game-table names.

| Evidence family | Required relationships | Acceptance condition |
|---|---|---|
| Effect semantics | Effect key → bonus type → stat operation; unit-set definition and membership; scope resolution | Every applied bonus resolves to a stat, operation and exact eligible unit keys without guessing from text |
| Unit experience | Rank → stat bonuses, eligible unit classes/sets, rank caps | Reproduce a rank-0 and rank-9 custom-battle card for a known unit |
| Ability lifecycle | Unit/character effect → enabled ability → phases; target filters; start/stop conditions; durations, charges and cooldowns | Separate self, aura and army targets; identify compatible sustained and burst states |
| Campaign sources | Faction traits, lord traits, ancillary/item effects and slots, skills that grant them, faction bundles and unit upgrades | Each buff has an acquisition path and scope; mutually exclusive options cannot stack |
| Dynamic progression | Tiger Court, Armies of Shang-Yang, Waaagh!/Scrap, Dwarf progression, Chaos gifts/authority and analogous rival systems | Preserve event conditions, unit-vs-army targets, repeat counts and hard caps |
| Army legality | Recruitment-pool and campaign caps, ability to expand caps, unit availability for each faction/lord pair | Demonstrate acquisition of 19 copies without treating absence of a static cap as proof |
| Engine arithmetic | Percent/flat combination, integer rounding, resistance caps, displayed speed conversion | Recover documented rules or validate against controlled cards; retain unresolved channels explicitly |

Discover actual table names and dependency closure through the available game
schema. Do not fabricate a relation from similar identifiers. Export only the
required decoded relations and bounded Lua evidence, preserving source keys,
hashes and row provenance. Acquisition code, not only positive buff bundles,
must be inspected for eligibility, replacements, consumption and caps.

The first end-to-end acceptance target is **one controlled Bhashiva/Iron Claw
card with known faction, lord skills, technologies, unit rank and active
conditions**. The conversation screenshot remains a useful observation but
lacks enough state to uniquely validate the reconstruction. If controlled game
state is unavailable, keep the ceiling unverified and use database invariants
for the recoverable parts; do not require the user to manually enumerate buffs.

After target/operation joins are complete, scan all lord and faction modifiers
before pruning candidates. Then enumerate compatible builds, enforcing skill
budgets, technology variants, equipment slots and dynamic restrictions. Report
separate permanent, sustainable and burst Pareto frontiers. Preserve candidates
outside the small-infantry slice if the question is broadened to all doomstacks.
