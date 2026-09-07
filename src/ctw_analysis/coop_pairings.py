"""Reproduce the issue #6 pairing study from a read-only, commit-locked atlas.

Run: python -m ctw_analysis.coop_pairings --ctw-root PATH --verify-regeneration
Only the Python standard library is required for this study.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sqlite3
import subprocess
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

from .coop_geography import build_geography
from .coop_diplomacy import GUIDE_RULES, EXCEPTIONS, classify, evidence_registry, policy_table

ROOT = Path(__file__).resolve().parents[2]
STUDY = ROOT / 'studies/coop_pairings'
ATLAS = 'data/campaign_map/campaign_atlas__wh3__8.1.1.gpkg'
INDEX = 'data/economy/faction_index__wh3__8.1.1.csv'
NOTION_URL = 'https://www.notion.so/3d33c519147b81d2b920e93cc2d8792b'
ISSUE_URL = 'https://github.com/OwenTanzer/computational-total-war-analysis/issues/6'
AUDIT_DATE = '2026-09-06'
BASELINE_PAIR = tuple(sorted(('wh3_dlc26_grn_gorbad_ironclaw','wh_main_grn_orcs_of_the_bloody_hand')))
INPUTS = ['AGENTS.md','context_catalog.json',ATLAS,INDEX,
          'data/campaign_map/README.md','data/campaign_map/VALIDATION.md','data/campaign_map/validation_report.json',
          *['data/campaign_map/starting_positions/'+p for p in ('README.md','dataset_manifest.json','schema_inventory.csv','script_audit.md','starting_positions_validation.json','army_starts.csv','partner_overrides.csv','source_exports/source_manifest.json','source_exports/custom_start_rules.json','source_exports/characters.csv')],
          'data/economy/README.md','data/economy/dataset_manifest.json','data/economy/schema_inventory__v1.csv',
          'data/economy/audit_report.json','data/faction_guides/README.md','data/faction_guides/queue.json',
          *[f'data/faction_guides/races/{r}.md' for r in sorted(GUIDE_RULES)]]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write_json(path, obj):
    path.write_text(json.dumps(obj,indent=2,ensure_ascii=False,sort_keys=True)+'\n',encoding='utf8',newline='\n')


def write_csv(path, rows, fields=None):
    fields = fields or list(rows[0])
    with path.open('w',encoding='utf8',newline='') as f:
        writer = csv.DictWriter(f,fieldnames=fields,lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def verify_source(root, lock_path=ROOT/'source_lock.json'):
    root = root.resolve()
    lock = read_json(lock_path)
    def git(*args):
        return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()
    require(git('rev-parse','HEAD') == lock['git_commit'],'Source HEAD differs from source_lock.json; review any lock update explicitly')
    require(read_json(root/'context_catalog.json')['snapshot'] == lock['snapshot'],'Source snapshot differs from lock')
    require(all((root/p).is_file() for p in INPUTS),'Required locked source inputs missing')
    require(not git('status','--porcelain','--untracked-files=all','--',*INPUTS),'Consumed source inputs have local changes')
    # Compare actual working files through Git filters as well as status. This catches
    # stale index/stat caches and avoids treating Windows checkout CRLF as drift.
    for path in INPUTS:
        actual = git('hash-object',f'--path={path}',path)
        expected = git('rev-parse',f'HEAD:{path}')
        require(actual == expected,f'Source bytes differ from locked Git blob: {path}')
    for name in ('campaign_map/validation_report.json','economy/audit_report.json'):
        report = read_json(root/'data'/name)
        require(report['status'] == 'passed' and not report.get('errors'),f'Source validation failed: {name}')
    queue = read_json(root/'data/faction_guides/queue.json')
    require({r['race_slug'] for r in queue['races']} == set(GUIDE_RULES),'Guide index coverage differs')
    require(all(r['status']=='completed' for r in queue['races']),'Guide index has unfinished races')
    return {'repository':lock['repository'],'git_commit':lock['git_commit'],'snapshot':lock['snapshot'],
            'source_lock_changed':False,'atlas_sha256':sha(root/ATLAS),
            'inputs': {p:{'git_blob':git('rev-parse',f'HEAD:{p}')} for p in INPUTS}}


def open_atlas(root):
    db = sqlite3.connect((root/ATLAS).resolve().as_uri()+'?mode=ro',uri=True)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA query_only=ON')
    return db


def validate(pairs, factions):
    keys = set(factions)
    require(len(keys)==104,f'Expected 104 playable keys, observed {len(keys)}')
    require(len(pairs)==math.comb(len(keys),2)==5356,f'Unexpected pair count: {len(pairs)}')
    seen = set()
    appearances = Counter()
    for p in pairs:
        a,b = p['faction_a_key'],p['faction_b_key']
        require(a in keys and b in keys and a < b,'Unresolved/noncanonical pair identifier')
        require((a,b) not in seen,'Duplicate unordered pair')
        seen.add((a,b)); appearances.update((a,b))
        require(p['proximity_class'] in {'Immediate','Regional','Extended','Distant','Unresolved'},'Incomplete geography')
        require(p['diplomatic_class'] in {'Clean','Workable','Special','Conflict'},'Incomplete diplomacy')
        require(p['evidence_ids'] and p['analytical_inference'] and p['diplomatic_caveat'],'Missing scoped evidence or uncertainty')
        require(p['included'] == (p['geographic_envelope'] and p['diplomatic_class']!='Conflict' and not p['treaty_eligibility_unresolved']),'Intersection inconsistent')
        if p['included']:
            require(p['geographic_distance'] is not None and all(p[k] is not None for k in ('world_x_a','world_y_a','world_x_b','world_y_b')),'Included pair lacks army points')
            if p['maritime_anchor_inference']:
                require(p['raster_hops'] is None and p['proximity_class']!='Immediate','Maritime adjacency asserted')
                require(max(p['land_anchor_gap_a'],p['land_anchor_gap_b'])<=25,'Maritime anchor gap violated')
            if p['proximity_class']=='Extended':
                require(p['shared_theater_keys'] and ((p['land_anchor_hops'] is not None and p['land_anchor_hops']<=6) or p['geographic_distance']<=75),'Extended gate violated')
        else:
            require(p['exclusion_reason'],'Rejected pair has no reason')
    require(set(appearances)==keys and set(appearances.values())=={103},'Every faction must occur in 103 pair rows')
    return ['104 canonical playable factions resolve in atlas and normalized index',
            '5356 unique sorted unordered pairs; every faction occurs 103 times',
            'Every pair has geography, diplomacy, source evidence, inference and uncertainty fields',
            'All included pairs pass independent geography/diplomacy gates; Extended gate verified',
            'All rejections explained; no null treated as numeric zero']


def objective_pressure(db):
    result = defaultdict(list)
    query = '''SELECT o.faction_key,o.objective_key,o.objective_type,c.target_key
               FROM objectives o JOIN objective_conditions c USING(objective_key)
               WHERE c.condition_type='faction' ORDER BY o.objective_key,c.condition_order'''
    for r in db.execute(query):
        result[(r['faction_key'],r['target_key'])].append(r['objective_key']+':'+r['objective_type'])
    return result


def generate(root, output, work):
    root,output,work = root.resolve(),output.resolve(),work.resolve()
    require(not output.is_relative_to(root) and not work.is_relative_to(root),'Outputs cannot be written inside the read-only CTW dependency')
    output.mkdir(parents=True,exist_ok=True); work.mkdir(parents=True,exist_ok=True)
    provenance = verify_source(root)
    with open_atlas(root) as db:
        metadata = dict(db.execute('SELECT key,value FROM metadata'))
        require(metadata['patch']=='8.1.1' and metadata['steam_build_id']=='24237342','Atlas snapshot mismatch')
        require(db.execute('PRAGMA integrity_check').fetchone()[0]=='ok','Atlas integrity failure')
        starts, pairs, calibration = build_geography(db)
        pressure = objective_pressure(db)
        source_coverage = [dict(r) for r in db.execute('SELECT * FROM coverage ORDER BY subject')]
        schema = [dict(r) for r in db.execute("SELECT name,type,sql FROM sqlite_master WHERE name IN ('faction_start_reference','faction_army_start_reference','campaign_army_starts','campaign_start_rules','campaign_start_partner_overrides','regions','provinces','region_points','region_adjacency','region_groups','strategic_nodes','strategic_links','objectives','objective_conditions') ORDER BY name")]
    with (root/INDEX).open(encoding='utf-8-sig',newline='') as f:
        index = list(csv.DictReader(f))
    factions = {f['faction_key']:f for f in index}
    require(len(index)==len(factions)==104,'Normalized index has duplicate/missing keys')
    require(set(factions)=={f['faction_key'] for f in starts},'Atlas/index playable-key mismatch')
    for s in starts:
        f = factions[s['faction_key']]
        require(s['subculture_key']==f['subculture_key'] and s['culture_key']==f['culture_key'],'Source identity disagreement')
        f.update(s)
    # Freeze check occurs BEFORE importing diplomatic outputs into any pair row.
    frozen = read_json(STUDY/'calibration.json')
    require(calibration==frozen,'Geographic calibration changed: review and refreeze rules before diplomacy')
    evidence = evidence_registry(root)
    for p in pairs:
        a,b = (factions[p[f'faction_{side}_key']] for side in ('a','b'))
        for side,f in (('a',a),('b',b)):
            p[f'faction_{side}_name'] = f['faction_name']
            p[f'race_{side}'] = f['race_slug']
            p[f'subculture_{side}'] = f['subculture_key']
        p.update(classify(a,b,pressure[(a['faction_key'],b['faction_key'])]+pressure[(b['faction_key'],a['faction_key'])]))
        require(set(p['evidence_ids'].split(';'))<=set(evidence),'Unresolved evidence ID')
        p['evidence_note'] = ' '.join(evidence[e]['source_fact'] for e in p['evidence_ids'].split(';'))
        p['included'] = p['geographic_envelope'] and p['diplomatic_class']!='Conflict' and not p['treaty_eligibility_unresolved']
        reasons = []
        if not p['geographic_envelope']: reasons.append(p['geographic_reason'])
        if p['diplomatic_class']=='Conflict': reasons.append('Diplomatic Conflict: '+p['analytical_inference'])
        if p['treaty_eligibility_unresolved']: reasons.append('Treaty eligibility unresolved')
        p['exclusion_reason'] = '; '.join(reasons)
    checks = validate(pairs,factions)
    included = [p for p in pairs if p['included']]
    pair_key=lambda p:(p['faction_a_key'],p['faction_b_key'])
    with (STUDY/'prior_capital_proxy_qualifiers.csv').open(encoding='utf8',newline='') as f:
        previous={pair_key(r):r for r in csv.DictReader(f)}
    current={pair_key(r):r for r in pairs}
    new_keys={pair_key(p) for p in included}
    repair=[]
    for key in sorted(set(previous)|new_keys):
        before,after=previous.get(key),current[key]
        repair.append({'faction_a_key':key[0],'faction_b_key':key[1],
            'faction_a_name':after['faction_a_name'],'faction_b_name':after['faction_b_name'],
            'previous_included':bool(before),'current_included':after['included'],
            'change':('retained' if before else 'added') if after['included'] else 'removed',
            'previous_proximity':before['proximity_class'] if before else None,
            'current_proximity':after['proximity_class'],
            'previous_diplomacy':before['diplomatic_class'] if before else None,
            'current_diplomacy':after['diplomatic_class'],
            'geographic_distance':after['geographic_distance'],'reason':after['exclusion_reason'] or after['geographic_reason']})
    write_csv(output/'start_repair_comparison.csv',repair)
    write_csv(output/'start_region_corrections.csv',[{'faction_key':f['faction_key'],'faction_name':f['faction_name'],
        'previous_capital_proxy':f['capital_region_key'],'human_start_region':f['start_region_key'],
        'primary_world_x':f['world_x'],'primary_world_y':f['world_y'],'position_kind':f['position_kind'],
        'nearest_land_anchor':f['nearest_land_region_key'],'script_rule_indexes':f['script_rule_indexes']} for f in starts])
    nearby = [p for p in pairs if not p['included'] and p['proximity_class'] in {'Immediate','Regional','Extended'}]
    counts = Counter(k for p in included for k in (p['faction_a_key'],p['faction_b_key']))
    unknown_counts = Counter(k for p in pairs if p['proximity_class']=='Unresolved' or p['treaty_eligibility_unresolved'] for k in (p['faction_a_key'],p['faction_b_key']))
    coverage = []
    for key,f in sorted(factions.items()):
        coverage.append({'faction_key':key,'faction_name':f['faction_name'],'race':f['race_slug'],
                         'start_region':f['start_region_key'],'capital_region':f['capital_region_key'],
                         'start_position_kind':f['position_kind'],'qualifying_partners':counts[key],
                         'unresolved_pair_count':unknown_counts[key],
                         'zero_partner_reason': ('no partner passes frozen geography and diplomatic policy; unresolved treaty eligibility remains explicit') if not counts[key] else '',
                         'recovered_baseline_partners':int(key in BASELINE_PAIR),
                         'baseline_underrepresentation':'not assessable: 123 of 124 baseline rows missing'})
    require(sum(c['qualifying_partners'] for c in coverage)==2*len(included),'Partner-count sum mismatch')
    baseline = next(p for p in pairs if (p['faction_a_key'],p['faction_b_key'])==BASELINE_PAIR)
    comparison = {'baseline_url':NOTION_URL,'baseline_parent_page_id':'3773c519-147b-81a9-9fe6-cc080b7475a9',
                  'retrieval_date':AUDIT_DATE,'retrieval_truncated':False,'unknown_blocks':[],
                  'reported_pre_audit_count':124,'reported_post_flag_count':123,'reported_shortlist_count':62,
                  'historical_erroneous_shortlist_label':61,'recovered_pair_rows':1,'missing_pair_rows':123,
                  'regional_groupings_recovered':0,'complete_pair_level_comparison':False,
                  'changed_classifications':'Only the named stale geography flag is comparable; no old class columns exist.',
                  'newly_discovered_pairs':'Not identifiable from the incomplete baseline; do not call generated-only rows new omissions.',
                  'underrepresented_factions':'Not identifiable: recovered row frequency is not the original enumeration frequency.',
                  'recovered_row_result':{'historical_pair':'Gorbad + Wurrzag','historical_status':'pre-audit candidate, already flagged geographically stale',
                                          **{k:baseline[k] for k in ('faction_a_key','faction_b_key','start_region_a','start_region_b','geographic_distance','centroid_distance','raster_hops','proximity_class','diplomatic_class','included','exclusion_reason')}}}
    caveats = [
        'All 104 primary army world points resolve from ESF plus static human startup rules. Runtime callback/teleport behavior is not playtested; later player choices excluded.',
        'Four human starts are maritime points without unique sea masks. Nearby land anchors support an explicit geographic inference, not a landing entitlement or movement route.',
        '70 maritime/special regions lack individual geometry; 72 lack a province. Province-less unknown terrain is excluded from graph traversal.',
        'Raster border paths are topological indicators, not passable movement routes or campaign turns. Islands may lack paths even when physically close.',
        'All 119 strategic links are trade-route segments. 261 teleportation nodes do not supply validated player access or traversal edges; no portal/sea-lane shortcut qualifies a pair.',
        'Generic numeric aversion, opening wars/treaties and all faction/lord/technology modifiers are absent from the consumed normalized coverage; analytical priors are explicit and are not exhaustive runtime diplomacy validation.',
        'Beastmen permitted-faction set and Golgfag alliance/team override remain unresolved and are withheld from qualification.',
        'Single-player faction objectives are pressures only, never automatic multiplayer war locks. Teammates are independent human factions, not a proposed confederation or vassal arrangement.',
        'Source guide validation is structural; this study does not replay Lua or launch a multiplayer game.',
        'Notion contains counts and audit plan, one named stale pair, no full rows or regional headings; complete baseline diff and underrepresentation claims are impossible.',
    ]
    report = {'status':'passed_with_documented_coverage_gaps','audit_date':AUDIT_DATE,'patch':'8.1.1','steam_build_id':24237342,
              'acceptance_complete':False,'issue_closure_recommended':False,'faction_count':len(factions),'pair_count':len(pairs),
              'qualifying_pair_count':len(included),'nearby_rejected_count':len(nearby),
              'prior_implementation_comparison':{'commit':'c169e19f154784759041677d1def85dd5844c946',
                  'previous_qualifiers':len(previous),'current_qualifiers':len(included),
                  'counts':dict(Counter(r['change'] for r in repair)),
                  'retained_changed_proximity':sum(r['change']=='retained' and r['previous_proximity']!=r['current_proximity'] for r in repair),
                  'scope':'Complete qualifying-set comparison with the prior implementation, NOT the incomplete historical Notion enumeration'},
              'proximity_counts':dict(sorted(Counter(p['proximity_class'] for p in pairs).items())),
              'diplomatic_counts_all_pairs':dict(sorted(Counter(p['diplomatic_class'] for p in pairs).items())),
              'qualifying_by_diplomacy':dict(sorted(Counter(p['diplomatic_class'] for p in included).items())),
              'qualifying_by_proximity':dict(sorted(Counter(p['proximity_class'] for p in included).items())),
              'zero_partner_factions':[c for c in coverage if not c['qualifying_partners']],
              'missing_start_factions':[{'key':k,'name':f['faction_name']} for k,f in sorted(factions.items()) if f['world_x'] is None],
              'maritime_start_factions':[{'key':k,'name':f['faction_name']} for k,f in sorted(factions.items()) if f['start_region_key'] is None],
              'checks':checks+['Source commit, snapshot and consumed Git blobs verified; SQLite read-only integrity passed',
                               '24 guide profiles and every evidence anchor resolved','Partner-count sum equals twice qualifying pairs'],
              'remaining_gaps':caveats,'source_validation_warnings':read_json(root/'data/campaign_map/validation_report.json')['warnings']}
    write_csv(work/'all_pairs.csv',pairs)
    write_csv(output/'qualifying_pairs__8.1.1.csv',included,list(pairs[0]))
    write_csv(output/'nearby_rejected.csv',nearby,list(pairs[0]))
    write_csv(output/'faction_coverage.csv',coverage)
    write_csv(output/'baseline_pair_comparison.csv',[comparison['recovered_row_result']])
    write_json(output/'baseline_comparison.json',comparison)
    write_json(output/'evidence_registry.json',evidence)
    write_json(output/'race_policy.json',policy_table())
    write_json(output/'coverage_report.json',report)
    write_json(output/'source_provenance.json',{**provenance,'atlas_metadata':metadata,'atlas_coverage':source_coverage,
                                              'atlas_schema_inventory':schema,'notion_baseline_url':NOTION_URL,
                                              'baseline_sha256':sha(STUDY/'baseline_september_6.md'),
                                              'geography_freeze_commit':'400dfbd',
                                              'starting_positions_validation':read_json(root/'data/campaign_map/starting_positions/starting_positions_validation.json'),
                                              'source_repair_pr':'https://github.com/OwenTanzer/computational-total-war/pull/6'})
    # Full faction-by-faction audit inventory, including subjects with missing starts.
    profiles = []
    for key,f in sorted(factions.items()):
        ids = [f"{f['race_slug']}_{i}" for i in range(len(GUIDE_RULES[f['race_slug']]))]
        ids += [e[0] for e in EXCEPTIONS if e[1]==key]
        profiles.append({'faction_key':key,'faction_name':f['faction_name'],'race':f['race_slug'],
                         'evidence_ids':';'.join(ids),'audit_status':'guide reviewed; generic modifier coverage incomplete'})
    write_csv(output/'faction_evidence.csv',profiles)
    theater_groups = defaultdict(list)
    for p in included: theater_groups[p['theater']].append(p)
    lines = ['# Regional enumeration','',f'{len(included)} pairs qualify under the frozen analytical policy. Implemented on the PR branch; awaiting review and merge.',
             '', 'All 104 primary army points resolve. This is exhaustive over the stated analytical rules; diplomatic and runtime uncertainties remain. See [coverage report](coverage_report.json) and [methodology](methodology.md).',
             '', 'Names are source faction labels. Every row links through stable keys in [the machine-readable table](qualifying_pairs__8.1.1.csv); evidence and caveats are retained there.','']
    summary = []
    for theater, group in sorted(theater_groups.items()):
        summary.append({'theater':theater,'qualifying_pairs':len(group),**{c:sum(p['diplomatic_class']==c for p in group) for c in ('Clean','Workable','Special')}})
        lines += [f'## {theater} ({len(group)})','', '| Faction A | Faction B | Proximity | Diplomacy | Evidence |', '|---|---|---|---|---|']
        for p in group:
            lines.append(f"| {p['faction_a_name']} | {p['faction_b_name']} | {p['proximity_class']} | {p['diplomatic_class']} | {p['evidence_ids']} |")
        lines.append('')
    (output/'regional_pairings.md').write_text('\n'.join(lines).rstrip()+'\n',encoding='utf8',newline='\n')
    write_csv(output/'regional_summary.csv',summary,['theater','qualifying_pairs','Clean','Workable','Special'])
    diff_lines = ['# Historical versus generated','',f'Historical page: {NOTION_URL}', '',
                  'The untruncated September 6 page contains the 124 / 123 / 62 counts and audit plan, but only one named pair and no regional groupings. The other 123 candidate identities, original proximity/diplomacy classes, regional assignments, 62-row shortlist, 53 pruned rows and nine later additions are missing.', '',
                  f"Gorbad + Wurrzag: {baseline['start_region_a']} to {baseline['start_region_b']}; primary armies {baseline['geographic_distance']} world units apart (region centroids {baseline['centroid_distance']}), {baseline['raster_hops']} raster borders; {baseline['proximity_class']} / {baseline['diplomatic_class']}; excluded. The stale flag is corroborated.",'',
                  f'{len(included)} generated qualifiers cannot be called newly discovered relative to the unrecovered 123 rows. Changed old class labels and systematic faction underrepresentation cannot be reconstructed. The counts never set a target for generation.', '',
                  'See [the recovered historical page](baseline_september_6.md), [one-row comparison](baseline_pair_comparison.csv), and [all-faction counts](faction_coverage.csv).']
    (output/'preliminary_vs_generated.md').write_text('\n'.join(diff_lines)+'\n',encoding='utf8',newline='\n')
    manifest = {p.name:sha(p) for p in sorted(output.iterdir()) if p.is_file() and p.name in GENERATED_FILES and p.name!='output_hashes.json'}
    write_json(output/'output_hashes.json',manifest)
    return report


GENERATED_FILES = {'qualifying_pairs__8.1.1.csv','nearby_rejected.csv','faction_coverage.csv','baseline_pair_comparison.csv',
                   'baseline_comparison.json','evidence_registry.json','race_policy.json','coverage_report.json',
                   'source_provenance.json','faction_evidence.csv','regional_pairings.md','regional_summary.csv',
                   'preliminary_vs_generated.md','start_repair_comparison.csv','start_region_corrections.csv','output_hashes.json'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ctw-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=STUDY)
    parser.add_argument('--work-dir',type=Path,default=ROOT/'work/coop_pairings')
    parser.add_argument('--verify-regeneration',action='store_true')
    args = parser.parse_args()
    report = generate(args.ctw_root,args.output,args.work_dir)
    if args.verify_regeneration:
        with tempfile.TemporaryDirectory(prefix='ctw-coop-') as tmp:
            other,work = Path(tmp)/'study',Path(tmp)/'work'
            generate(args.ctw_root,other,work)
            for name in sorted(GENERATED_FILES):
                require((args.output/name).read_bytes()==(other/name).read_bytes(),f'Non-deterministic artifact: {name}')
            require((args.work_dir/'all_pairs.csv').read_bytes()==(work/'all_pairs.csv').read_bytes(),'Non-deterministic all-pair universe')
        print('Deterministic regeneration verified: all generated study files and all-pairs CSV are byte-identical.')
    print(json.dumps({k:report[k] for k in ('status','acceptance_complete','faction_count','pair_count','qualifying_pair_count','nearby_rejected_count','qualifying_by_diplomacy','qualifying_by_proximity')},indent=2))


if __name__ == '__main__':
    main()
