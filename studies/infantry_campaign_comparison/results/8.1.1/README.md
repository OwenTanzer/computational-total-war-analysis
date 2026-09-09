# Iron Claws and competing infantry: first data comparison

**Campaign ceiling: unresolved.** Iron Claws occupy a strong combination of dimensions, but the available reconstruction does not establish the highest-stat doomstack.

Source: [5d25716de3d1](https://github.com/OwenTanzer/computational-total-war/tree/5d25716de3d18d0006f95d7aa623a7c062d72834) — patch 8.1.1, Ultra scale. See [methodology](../../methodology.md) and the [reviewed modifier selections](../../profiles.json).

## Full base screen

Read 2,000 roster rows (1,669 distinct unit keys); 186 meet the small-target melee-infantry filters and static 19-copy cap check. Dynamic recruitment availability is not yet certified. Rankings count distinct unit keys, including different variants with the same name.

| Dimension | Iron Claw value | Competition rank | Highest base value |
|---|---:|---:|---|
| Unit health | 8800.00 | 109 / 186 | Zombies: 12320.00 |
| Armour | 60.00 | 74 / 186 | Chosen of Khorne: 130.00 |
| Melee attack | 40.00 | 26 / 186 | Wrathmongers: 60.00 |
| Melee defence | 46.00 | 21 / 186 | Chosen of Slaanesh (Hellscourges): 70.00 |
| Speed (source units) | 4.40 | 21 / 186 | Plague Toads of Nurgle: 6.50 |
| Raw attack-capacity proxy | 1052.63 | 36 / 186 | Blessed Saurus Warriors (Shields): 1729.73 |
| Armour-piercing attack-capacity proxy | 800.00 | 9 / 186 | Hammerers: 976.19 |

Iron Claws are on the **base Pareto frontier**, alongside 98 other candidates. This broad frontier reflects trade-offs across many axes; it is not a ranking of elite units. No base candidate is removed from future campaign research.

Attack-capacity proxies assume all models attack at the nominal interval and every attack connects. They are not battle damage measurements. Armour-piercing capacity is part of total capacity, not additional damage.

## Selected base cards

| Unit | Models | Health | Armour | Attack / defence | Weapon normal + piercing | Speed (source) |
|---|---:|---:|---:|---:|---:|---:|
| Iron Claw Tiger Warriors | 80 | 8800 | 60 | 40 / 46 | 12 + 38 | 4.4 |
| Hammerers | 100 | 10000 | 100 | 46 / 38 | 14 + 41 | 2.8 |
| Black Orcs (Great Weapons) | 80 | 10800 | 110 | 38 / 32 | 14 + 36 | 2.9 |
| Chosen of Slaanesh (Hellscourges) | 80 | 10480 | 120 | 42 / 70 | 34 + 8 | 3.3 |
| Chosen of Nurgle (Great Weapons) | 80 | 11440 | 120 | 43 / 51 | 12 + 38 | 2.8 |

## Known modifiers at a rank-9 neutral condition

The ledger contains **63 reviewed source effect rows** across five profiles. The following figures are **base stats plus selected known modifiers**, excluding native rank stat gains, unresolved faction systems, items, auras and other effects. They are neither complete cards nor attainable ceilings. Unequal missing coverage prevents using this table to declare a campaign winner.

| Lord / unit | Armour subtotal | Attack / defence subtotal | Physical resistance subtotal | Weapon strength subtotal |
|---|---:|---:|---:|---:|
| Bhashiva / Iron Claw Tiger Warriors | 85 | 50 / 65 | 10% | 50.00 |
| Thorgrim / Hammerers | 110 | 57 / 38 | 30% | 73.70 |
| Grimgor / Black Orcs (Great Weapons) | 132 | 48 / 37 | 0% | 67.50–69.03 |
| Sigvald / Chosen of Slaanesh (Hellscourges) | 152 | 59 / 86 | 10% | 46.00 |
| Festus / Chosen of Nurgle (Great Weapons) | 152 | 51 / 56 | 0% | 63.50 |

The weapon-strength range exposes two possible flat/percentage application orders; it is not an engine-certified bound. Attacking-ambush and defending-siege conditions are separate rows in the accompanying CSV, never combined.

Notable source-backed contributions:

* Bhashiva: +6 attack/+6 defence from terminal Unyielding, +10% physical resistance from Deadly & Graceful, and +5 defence at unit rank 7+ from Blades of the Bastion. Drill Training and Jade Stance supply +25 armour/+8 defence together. These are explicit text-supported targets; the underlying engine unit-set joins remain unavailable.
* Thorgrim's Hammerers: +15% physical resistance from High King, +10% at rank 7+ from Honoured by Grimnir, and +5% from Royal Guard. Selected weapon-strength bonuses total +34% in the neutral subtotal.
* Festus: Hideous Amputation supplies +3% weapon strength per experience rank to Great Weapons units—+27% at rank 9, separate from missing native experience bonuses.
* Sigvald's Hellscourges retain a much more defensive profile; they are a useful alternative to a damage-first comparison.

## What prevents a ceiling verdict

Effect-to-bonus operations and unit-set membership, native experience scaling, complete item/trait acquisition, ability activation/phase and targeting relations, faction upgrades/rituals and their caps, and dynamic recruitment limits must be resolved before an exhaustive campaign optimizer can run. Raw Ferocious Ambush phase data contains a 20-second duration, but missing activation relations prevent treating it as a sustained bonus or a verified peak stack.

The present result supports **a strong, mobile, armour-piercing infantry package**, not an absolute numerical supremacy claim.
