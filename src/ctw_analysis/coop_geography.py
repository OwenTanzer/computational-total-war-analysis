"""Diplomacy-independent army-start geography. World units are not turns."""
from collections import defaultdict, deque
from itertools import combinations
from math import hypot


def distances(graph, start):
    if start not in graph:
        return {}
    result = {start: 0}
    queue = deque([start])
    while queue:
        node = queue.popleft()
        for neighbor in sorted(graph[node]):
            if neighbor not in result:
                result[neighbor] = result[node] + 1
                queue.append(neighbor)
    return result


def classify(distance, hops, same_province, neighboring_province, shared_theater):
    if distance is None:
        return 'Unresolved', False, 'Capital/start geometry unavailable'
    if same_province or (hops is not None and hops <= 1 and distance <= 100):
        return 'Immediate', True, 'Same province or adjacent starts within 100 logical units'
    if distance <= 100 and (neighboring_province or (hops is not None and hops <= 4)):
        return 'Regional', True, 'Within 100 units with neighboring provinces or at most four raster borders'
    if distance <= 150 and (shared_theater or neighboring_province or (hops is not None and hops <= 6)):
        retained = bool(shared_theater and ((hops is not None and hops <= 6) or distance <= 75))
        return 'Extended', retained, ('Shared atlas theater and either at most six raster borders or at most 75 logical units' if retained
                                    else 'Extended requires shared atlas theater AND (at most six raster borders OR at most 75 logical units)')
    return 'Distant', False, 'Outside frozen geographic envelope'


def build_geography(db):
    starts = [dict(r) for r in db.execute('SELECT * FROM faction_army_start_reference ORDER BY faction_key')]
    overrides = {(r['faction_key'],r['partner_key']):dict(r) for r in db.execute('SELECT * FROM campaign_start_partner_overrides')}
    regions = {r['region_key']: dict(r) for r in db.execute(
        'SELECT region_key,province_key,geometry_status,centroid_x,centroid_y FROM regions')}
    graph = {k: set() for k, r in regions.items() if r['province_key'] and r['centroid_x'] is not None}
    province_edges = set()
    for edge in db.execute('SELECT region_a,region_b FROM region_adjacency ORDER BY region_a,region_b'):
        a, b = edge
        # Unknown terrain is a huge raster mask, not a traversable shortcut.
        if a in graph and b in graph:
            graph[a].add(b)
            graph[b].add(a)
            pa, pb = regions[a]['province_key'], regions[b]['province_key']
            if pa != pb:
                province_edges.add(tuple(sorted((pa, pb))))
    theaters = defaultdict(set)
    for group, region in db.execute("SELECT region_group_key,region_key FROM region_groups WHERE region_group_key GLOB 'cai_region_hint_area_*' ORDER BY 1,2"):
        theaters[region].add(group)
    nodes = [dict(r) for r in db.execute('SELECT * FROM strategic_nodes ORDER BY node_key')]
    node_by_key = {n['node_key']: n for n in nodes}
    links = [dict(r) for r in db.execute('SELECT * FROM strategic_links ORDER BY link_id')]
    route_context = defaultdict(set)
    for link in links:
        for side in ('from_node_key', 'to_node_key'):
            node = node_by_key.get(link[side])
            if node and node['region_key'] in regions:
                route_context[node['region_key']].add(link['network_key'])
    paths = {key:distances(graph,key) for key in {f['nearest_land_region_key'] for f in starts}}
    pairs = []
    for original_a, original_b in combinations(starts, 2):
        a,b=dict(original_a),dict(original_b)
        changed=[]
        for f,partner in ((a,b),(b,a)):
            override=overrides.get((f['faction_key'],partner['faction_key']))
            if override:
                f.update(override)
                f['nearest_land_region_key']=f['start_region_key']
                changed.append(f['faction_key'])
        ra, rb = a['start_region_key'], b['start_region_key']
        aa, ab = a['nearest_land_region_key'], b['nearest_land_region_key']
        pa, pb = regions.get(ra,{}).get('province_key'),regions.get(rb,{}).get('province_key')
        anchor_pa,anchor_pb=regions.get(aa,{}).get('province_key'),regions.get(ab,{}).get('province_key')
        d = None if any(f[c] is None for f in (a,b) for c in ('world_x','world_y')) else hypot(a['world_x']-b['world_x'], a['world_y']-b['world_y'])
        cd = hypot(regions[ra]['centroid_x']-regions[rb]['centroid_x'],regions[ra]['centroid_y']-regions[rb]['centroid_y']) if ra and rb else None
        maritime=not (ra and rb)
        anchor_hops = paths[aa].get(ab)
        hops = None if maritime else anchor_hops
        same = bool(pa and pb and pa == pb)
        adjacent = bool(anchor_pa and anchor_pb and tuple(sorted((anchor_pa,anchor_pb))) in province_edges)
        shared = sorted(theaters[aa] & theaters[ab])
        cls, envelope, reason = classify(d, anchor_hops, same, adjacent, shared)
        if maritime:
            if max(a['nearest_land_distance'],b['nearest_land_distance'])>25:
                envelope=False;reason='Maritime nearest-land gap exceeds frozen 25-world-unit anchor bound'
            elif cls=='Immediate':
                cls='Regional';reason='Coastal primary army points within 100 world units, with nearby land anchors; no maritime adjacency asserted'
            else:
                reason+='; topology/theaters use descriptive coastal anchors, not a verified sea route'
        reason=reason.replace('logical units','world units')
        ta, tb = sorted(theaters[aa]), sorted(theaters[ab])
        label = ' / '.join(shared) if shared else ' <-> '.join(sorted(' / '.join(t) or 'unmapped' for t in (ta,tb)))
        record = {'faction_a_key': a['faction_key'], 'faction_b_key': b['faction_key'],
                  'start_region_a': ra, 'start_region_b': rb, 'province_a': pa, 'province_b': pb,
                  'geographic_distance': round(d,6) if d is not None else None,
                  'distance_basis':'primary human army world coordinates',
                  'centroid_distance': round(cd,6) if cd is not None else None,
                  'world_x_a':a['world_x'],'world_y_a':a['world_y'],'world_x_b':b['world_x'],'world_y_b':b['world_y'],
                  'land_anchor_a':aa,'land_anchor_b':ab,'land_anchor_hops':anchor_hops,
                  'land_anchor_gap_a':a['nearest_land_distance'],'land_anchor_gap_b':b['nearest_land_distance'],
                  'maritime_anchor_inference':maritime,'partner_start_override':';'.join(changed),
                  'raster_hops': hops, 'same_province': same, 'neighboring_province': adjacent,
                  'shared_theater_keys': ';'.join(shared), 'theater': label.replace('cai_region_hint_area_', ''),
                  'proximity_class': cls, 'geographic_envelope': envelope, 'geographic_reason': reason,
                  'geometry_status_a': a['position_kind'],
                  'geometry_status_b': b['position_kind'],
                  'route_networks_a': ';'.join(sorted(route_context[ra])),
                  'route_networks_b': ';'.join(sorted(route_context[rb])),
                  'strategic_note': 'Caravan/convoy links are context only; portal nodes lack general traversal eligibility; no shortcut inferred',
                  'starting_position_caveat':'Static human startup rules; later choices excluded. Maritime land anchors are descriptive; not movement routes. Secondary forces do not set primary distance.',
                  'island_or_disconnected': d is not None and hops is None}
        pairs.append(record)
    observed = sorted(p['geographic_distance'] for p in pairs if p['geographic_distance'] is not None)
    calibration = {'method': 'Nearest-rank empirical quantiles, 104 primary human army world points with pair-specific overrides; no diplomatic input',
                   'distance_quantiles': {str(q): observed[int((len(observed)-1)*q)] for q in (.01,.025,.05,.1,.2,.25,.5,.75,.9)},
                   'factions': len(starts), 'resolved_army_points': sum(f['world_x'] is not None for f in starts),
                   'maritime_primary_points':sum(f['start_region_key'] is None for f in starts),
                   'region_graph_nodes': len(graph), 'region_graph_edges': sum(map(len,graph.values()))//2,
                   'strategic_node_count': len(nodes), 'strategic_link_count': len(links),
                   'strategic_networks': sorted({n['network_key'] for n in nodes if n['network_key']}),
                   'freeze': 'v3: primary army world-point distance; retain 100/150/75 boundaries and land rules. Maritime anchors require gap <=25, use anchor topology/theaters, cannot be Immediate, never assert a sea route. Extended shared theater AND (anchor hops <=6 OR distance <=75). Frozen before diplomacy.'}
    return starts, pairs, calibration
