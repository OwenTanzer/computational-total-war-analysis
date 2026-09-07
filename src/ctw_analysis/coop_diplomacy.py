"""Inspectable analytical policy over source identities and scoped guide evidence.

Classes describe an ordinary diplomatic ecosystem, not engine-enforced team legality.
No geography is accepted here. Evidence absence never establishes a zero modifier.
"""
from itertools import combinations_with_replacement

HUMANS = {'empire', 'bretonnia', 'kislev', 'grand_cathay'}
ORDER = HUMANS | {'dwarfs', 'high_elves', 'wood_elves', 'lizardmen'}
CHAOS = {'warriors_of_chaos', 'norsca', 'beastmen', 'daemons_of_chaos', 'khorne', 'nurgle', 'slaanesh', 'tzeentch', 'chaos_dwarfs'}
VAMPIRES = {'vampire_counts', 'vampire_coast'}
GODS = {'khorne','nurgle','slaanesh','tzeentch'}
PATRONS = {'wh3_dlc20_chs_azazel':'slaanesh','wh3_dlc20_chs_sigvald':'slaanesh',
           'wh3_dlc20_chs_festus':'nurgle','wh3_dlc20_chs_valkia':'khorne','wh3_dlc20_chs_vilitch':'tzeentch'}
RIVALS = {frozenset(('khorne','slaanesh')), frozenset(('nurgle','tzeentch'))}

# Exact source substrings are verified and resolved to line numbers during every run.
# Notes are paraphrases; scopes are deliberately narrower than a whole alignment bloc.
GUIDE_RULES = {
 'beastmen': [('Beastmen diplomacy is force-restricted', 'Restricted treaty set; permitted-faction membership and teammate bypass are not enumerated by the guide; positive deals reduce Bestial Rage for five turns.')],
 'bretonnia': [('Human Bretonnian factions are exempt', 'Human confederation cooldown exemption is not permission to absorb a human teammate.')],
 'chaos_dwarfs': [('Each successful usurpation increments', 'Tower-seat usurpation causes a five-turn diplomatic penalty; coordinate seat claims.')],
 'daemons_of_chaos': [('No separate faction-specific cult', 'Guide establishes no bespoke diplomacy override; generic aversion and dedication-state modifiers remain unmeasured.')],
 'dark_elves': [('Activating Death Night creates', 'Har Ganeth Blood Voyage is a forced vassal targeting occupied Ulthuan settlements; not a general alliance ban.'), ('The 6–9 and 10 bands add', 'Hag Graef gains conditional +25/+50 daemon relations at high possession; not a permanent faction-wide alliance guarantee.')],
 'dwarfs': [('peace and positive diplomacy reduce', 'Grudge accumulation responds to hostile conduct; positive diplomacy reduces it.'), ('A region adjacent to territory owned', 'Different allied Dwarf owners can enable conditional Deeps trade/diplomacy benefits.')],
 'empire': [('While this system operates', 'Reikland Elector politics replaces ordinary confederation/NAP paths; does not establish a general military-alliance ban.')],
 'grand_cathay': [('no distinct Grand Cathay campaign rule was found', 'Guide found no distinct diplomatic replacement; generic faction modifiers remain outside coverage.')],
 'greenskins': [('the loser is AI-controlled', 'Leader-defeat confederation requires an AI loser; it cannot consume the human teammate.')],
 'high_elves': [('The alliance actions unlock', 'Eataine can unlock Champion actions through alliances with other legendary High Elf factions.')],
 'khorne': [('no Khorne-specific confederation', 'No bespoke diplomacy override established; absence does not imply zero generic aversion.')],
 'kislev': [('The former supporter race', 'Old supporter-race forced confederation and intra-Kislev war ban are obsolete; ordinary diplomacy applies.')],
 'lizardmen': [('Allied province capitals can supply', 'Allied province capitals support the Geomantic Web; Nakai and Oxyotl use documented variants.')],
 'norsca': [('Tribal Confederation as defeating', 'Leader-defeat tribal confederation is not an ordinary alliance restriction; human-target applicability is not proven here.')],
 'nurgle': [('The installed script applies no diplomacy test', 'Epidemius can count negatively plagued non-Nurgle allies; alliance status provides no documented protection.')],
 'ogre_kingdoms': [('all Ogre Kingdoms factions are immune', 'Ogre trespass diplomacy immunity is official-source-only in the guide; battle confederation requires an AI loser.')],
 'skaven': [('when the factions are not teammates', 'Vermintide war declaration explicitly excludes teammates; this is not blanket protection against all Under-City damage.')],
 'slaanesh': [('The ritual target explicitly excludes human factions', 'N\'Kari forced seduction cannot target humans; this does not make third-party vassal diplomacy harmless.')],
 'tomb_kings': [('When another relevant Tomb Kings faction is human', 'Human participants lock Cult confederation rituals.'), ('the same mission key fails for every other eligible human', 'Books of Nagash are competitive shared multiplayer rewards; team ownership does not duplicate them.')],
 'tzeentch': [('Grand Scheme completion applies a theatre-specific', 'Changeling Schemes change the world by theater; effects on a partner require coordination, not a universal immunity assumption.')],
 'vampire_coast': [('Alliances remain ordinary diplomacy', 'Coast cannot confederate; alliances can transfer Shanty verses.')],
 'vampire_counts': [('diplomacy is +30 with Warriors of Chaos', 'Barrow Legion has +30 WoC/Beastmen/Norsca relations and faction Chaos-attrition immunity.')],
 'warriors_of_chaos': [('It does not prove that every destroyed', 'Homeland vassalization is faction/settlement-specific and does not guarantee revival.'), ('Only **Warhost of the Apocalypse and Shadow Legion**', 'Only Archaon/Be\'lakor have the final-settlement forced WoC confederation route; other WoC do not.')],
 'wood_elves': [('locks that specific rite for every human Wood Elf faction', 'Rebirth completion is global and one-time in co-op; Ariel is globally unique.'), ('she is barred from confederating Wood Elves generally', 'Drycha can confederate only Argwylon; not a general ban on Wood Elf alliances.')],
}

# id, subject key, target races (empty = any), class override, race guide,
# exact source anchor, source fact, analytical implication, viability unresolved.
EXCEPTIONS = [
 ('huntsmarshal_lizards','wh2_dlc13_emp_the_huntmarshals_expedition',{'lizardmen'},'Special','empire','with a multiplayer-teammate exception',
  'Lizardmen diplomacy disabled except payments/war/peace, with explicit teammate exception.', 'Team exception permits pairing; surrounding Lizardmen diplomacy and Hostility still need coordination.',False),
 ('repanse_undead','wh2_dlc14_brt_chevaliers_de_lyonesse',VAMPIRES|{'tomb_kings'},'Conflict','bretonnia','-80 diplomatic relations with Vampire Counts',
  'Repanse has -80 relations with all three undead races.', 'Structural anti-undead ecosystem overrides a neutral Tomb King baseline.',False),
 ('arkhan_tombs','wh2_dlc09_tmb_followers_of_nagash',{'tomb_kings'},'Conflict','tomb_kings','-60 relations with Tomb Kings and +40',
  'Arkhan starts at -60 Tomb King and +40 Vampiric Undead relations.', 'Arkhan is not treated as a clean same-race partner.',False),
 ('arkhan_vampires','wh2_dlc09_tmb_followers_of_nagash',VAMPIRES,'Clean','tomb_kings','-60 relations with Tomb Kings and +40',
  'Arkhan starts with +40 Vampiric Undead relations.', 'Positive cross-race bridge supports a shared undead ecosystem.',False),
 ('arkhan_living','wh2_dlc09_tmb_followers_of_nagash',ORDER,'Conflict','tomb_kings','-60 relations with Tomb Kings and +40',
  'Arkhan has a distinct Vampiric Undead affinity rather than the ordinary Tomb King relationship pattern.', 'Apply the opposed living/undead ecosystem prior to Arkhan; this is an inference, not an explicit universal war lock.',False),
 ('azazel_humans','wh3_dlc20_chs_azazel',HUMANS,'Workable','warriors_of_chaos','**+80 diplomatic relations with Empire',
  'Azazel has +80 relations with Empire/Kislev/Cathay/Bretonnia; seduction excludes human targets.', 'Positive bridge allows analytical Workable, but third-party Chaos hostility is not erased.',False),
 ('kemmler_chaos','wh2_dlc11_vmp_the_barrow_legion',{'warriors_of_chaos','beastmen','norsca'},'Workable','vampire_counts','diplomacy is +30 with Warriors of Chaos',
  'Kemmler has +30 WoC/Beastmen/Norsca diplomacy and Chaos attrition immunity.', 'Explicit bridge supports coordination with these races, not all Daemons.',False),
 ('malus_daemons','wh2_main_def_hag_graef',GODS|{'daemons_of_chaos'},'Workable','dark_elves','The 6–9 and 10 bands add',
  'High possession supplies +25/+50 daemon diplomacy.', 'Conditional bridge, not permanent Clean compatibility.',False),
 ('golgfag_contracts','wh3_dlc26_ogr_golgfag',set(),'Special','ogre_kingdoms','The Maneaters cannot conclude military alliances',
  'Maneaters cannot make military/defensive alliances or vassal agreements; client offers exclude enemies of his team.', 'Guide recognizes team context but does not prove a lobby override of the alliance ban; withhold qualification.',True),
 ('nakai_vassal','wh2_dlc13_lzd_spirits_of_the_jungle',set(),None,'lizardmen','outside factions cannot independently declare war or peace',
  'Defenders forced vassal has locked war/peace and cannot break from Nakai.', 'Coordinate settlement gifting; no general anti-co-op restriction inferred.',False),
 ('aislinn_gifts','wh3_dlc27_hef_aislinn',set(),None,'high_elves','Aislinn cannot use ordinary region trading',
  'Aislinn gifts settlements to six playable High Elf factions and cannot trade regions normally.', 'Do not promise ordinary reciprocal region trading or a fixed maritime start.',False),
 ('epidemius_plagues','wh3_dlc25_nur_epidemius',set(),None,'nurgle','The installed script applies no diplomacy test',
  'Non-Nurgle allies can count in the negative-plague Tally.', 'Cross-race allies need plague coordination; downgrade Clean to Workable.',False),
 ('eshin_contracts','wh2_main_skv_clan_eshin',{'skaven'},'Workable','skaven','It also unlocks diplomacy with a positively regarded issuing clan',
  'Greater Clan Contracts change issuer/target standing and unlock positive-clan diplomacy; Anarchy excludes humans.', 'Same-race classification accounts for contract friction, not automatic betrayal of a human.',False),
 ('settra_vassal','wh2_dlc09_tmb_khemri',set(),None,'tomb_kings',"Khemri cannot be made anyone's vassal",
  'All vassal actions against Khemri are disabled.', 'Pairings must use independent teammates, not a proposed Settra-vassal workaround.',False),
 ('khalida_lahmia','wh2_dlc09_tmb_lybaras',set(),None,'tomb_kings','permanently unable to make peace with the Lahmian Sisterhood',
  'Khalida has permanent no-peace with the nonplayable Lahmian Sisterhood.', 'Do not generalize this scripted lock to every playable vampire.',False),
 ('sayl_treaties','wh3_dlc27_nor_sayl',set(),None,'norsca','the automatic below-zero war listener is inert',
  'Sayl Manipulations alter treaties; automatic below-zero Confidence war listener is inert in 8.1.1.', 'Coordinate manipulation targets; do not infer compulsory teammate war from the stale listener.',False),
 ('changeling_schemes','wh3_dlc24_tze_the_deceivers',set(),None,'tzeentch','Grand Scheme completion applies a theatre-specific',
  'Schemes make theater-specific world changes and rifts have scripted progression.', 'Compatible partners require scheme coordination; no unconditional global travel shortcut.',False),
]


def race_baseline(a, b):
    """Explicit analyst prior; generic numeric aversion matrix is absent from the lock."""
    if a == b:
        return 'Clean', 'Same-race ecosystem prior'
    if frozenset((a,b)) in RIVALS:
        return 'Conflict', 'Rival-god ecosystem prior; no numeric aversion claimed'
    if a in ORDER and b in ORDER:
        if 'wood_elves' in (a,b) or 'lizardmen' in (a,b) or {a,b} == {'dwarfs','high_elves'}:
            return 'Workable', 'Order-adjacent but distinct territorial/diplomatic ecosystem prior'
        return 'Clean', 'Compatible Order ecosystem prior'
    if a in CHAOS and b in CHAOS:
        return 'Workable', 'Chaos ecosystem prior with patron/vassal competition'
    if a in VAMPIRES and b in VAMPIRES:
        return 'Clean', 'Shared vampiric ecosystem prior'
    if 'ogre_kingdoms' in (a,b):
        return 'Workable', 'Ogre mercenary-neutral ecosystem prior; faction restrictions take precedence'
    if 'tomb_kings' in (a,b):
        other = b if a == 'tomb_kings' else a
        return ('Workable','Independent Tomb King coexistence prior') if other in ORDER|{'dark_elves'} else ('Conflict','Opposed Tomb King ecosystem prior')
    if a in ORDER or b in ORDER:
        return 'Conflict', 'Opposed surrounding diplomatic ecosystems prior'
    return 'Workable', 'Non-Order pragmatic-alliance prior; not a numeric diplomatic guarantee'


def evidence_registry(root):
    registry = {}
    def add(key,race,anchor,fact):
        path = f'data/faction_guides/races/{race}.md'
        lines = (root/path).read_text(encoding='utf8').splitlines()
        hits = [i for i,line in enumerate(lines,1) if anchor in line]
        if not hits:
            raise ValueError(f'Unresolved source evidence {key}: {anchor}')
        registry[key] = {'path':path,'line':hits[0],'anchor':anchor,'source_fact':fact}
    for race, rules in GUIDE_RULES.items():
        for i,(anchor,fact) in enumerate(rules):
            add(f'{race}_{i}',race,anchor,fact)
    for key,_,_,_,race,anchor,fact,_,_ in EXCEPTIONS:
        add(key,race,anchor,fact)
    return registry


def classify(a,b,objective_pressures=()):
    ra,rb = a['race_slug'],b['race_slug']
    cls, inference = race_baseline(ra,rb)
    rules = [f'{r}_{i}' for r in sorted({ra,rb}) for i in range(len(GUIDE_RULES[r]))]
    notes = [inference]
    unresolved = False
    patron_a,patron_b = PATRONS.get(a['faction_key'],ra),PATRONS.get(b['faction_key'],rb)
    if frozenset((patron_a,patron_b)) in RIVALS:
        cls = 'Conflict'
        notes.append('Marked WoC patron overrides same-race/broad Chaos prior; rival-god conflict is analytical inference')
    for key,subject,targets,override,_,_,_,implication,unknown in EXCEPTIONS:
        for x,y in ((a,b),(b,a)):
            if x['faction_key'] == subject and (not targets or y['race_slug'] in targets):
                rules.append(key)
                notes.append(implication)
                unresolved |= unknown
                if override:
                    cls = override
                if key in ('epidemius_plagues','sayl_treaties','changeling_schemes') and cls == 'Clean' and ra != rb:
                    cls = 'Workable'
    if 'beastmen' in (ra,rb):
        unresolved = True
        if cls != 'Conflict':
            cls = 'Special'
        notes.append('Beastmen permitted-faction membership and multiplayer exception unresolved; no qualification asserted')
    if ra == rb and ra in {'chaos_dwarfs','tomb_kings','wood_elves'} and cls == 'Clean':
        cls = 'Workable'
        notes.append('Shared seat/Book/forest progression requires coordination')
    if objective_pressures:
        if cls == 'Clean':
            cls = 'Workable'
        notes.append('Partner appears in single-player faction objective(s); not treated as a multiplayer forced-war lock')
    return {'diplomatic_class':cls,'treaty_eligibility_unresolved':unresolved,
            'diplomacy_evidence_status':'Partial: guide evidence plus analytical prior; generic modifier matrix unmeasured',
            'evidence_ids':';'.join(sorted(set(rules))), 'analytical_inference':' '.join(notes),
            'diplomatic_caveat':'Generic numeric aversion, opening treaties, all faction/lord/technology modifiers and multiplayer runtime behavior are not exhaustively exported; classes are analytical, not verified team legality.',
            'single_player_objective_pressure':';'.join(sorted(objective_pressures))}


def policy_table():
    return [{'race_a':a,'race_b':b,'class':race_baseline(a,b)[0],'inference':race_baseline(a,b)[1]}
            for a,b in combinations_with_replacement(sorted(GUIDE_RULES),2)]
