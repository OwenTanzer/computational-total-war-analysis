"""Diplomacy-independent atlas geography. All distances are logical units, not turns."""
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
    starts = [dict(r) for r in db.execute('SELECT * FROM faction_start_reference ORDER BY faction_key')]
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
    paths = {f['faction_key']: distances(graph, f['capital_region_key']) for f in starts}
    pairs = []
    for a, b in combinations(starts, 2):
        ra, rb = a['capital_region_key'], b['capital_region_key']
        pa, pb = a['province_key'], b['province_key']
        d = None if any(f[c] is None for f in (a,b) for c in ('centroid_x','centroid_y')) else hypot(a['centroid_x']-b['centroid_x'], a['centroid_y']-b['centroid_y'])
        hops = paths[a['faction_key']].get(rb)
        same = bool(pa and pb and pa == pb)
        adjacent = bool(pa and pb and tuple(sorted((pa,pb))) in province_edges)
        shared = sorted(theaters[ra] & theaters[rb])
        cls, envelope, reason = classify(d, hops, same, adjacent, shared)
        ta, tb = sorted(theaters[ra]), sorted(theaters[rb])
        label = ' / '.join(shared) if shared else ' <-> '.join([' / '.join(t) or 'unmapped' for t in (ta,tb)])
        record = {'faction_a_key': a['faction_key'], 'faction_b_key': b['faction_key'],
                  'start_region_a': ra, 'start_region_b': rb, 'province_a': pa, 'province_b': pb,
                  'centroid_distance': round(d,6) if d is not None else None,
                  'raster_hops': hops, 'same_province': same, 'neighboring_province': adjacent,
                  'shared_theater_keys': ';'.join(shared), 'theater': label.replace('cai_region_hint_area_', ''),
                  'proximity_class': cls, 'geographic_envelope': envelope, 'geographic_reason': reason,
                  'geometry_status_a': regions[ra]['geometry_status'] if ra in regions else 'missing_capital',
                  'geometry_status_b': regions[rb]['geometry_status'] if rb in regions else 'missing_capital',
                  'route_networks_a': ';'.join(sorted(route_context[ra])),
                  'route_networks_b': ';'.join(sorted(route_context[rb])),
                  'strategic_note': 'Caravan/convoy links are context only; portal nodes lack general traversal eligibility; no shortcut inferred',
                  'island_or_disconnected': d is not None and hops is None}
        pairs.append(record)
    observed = sorted(p['centroid_distance'] for p in pairs if p['centroid_distance'] is not None)
    calibration = {'method': 'Nearest-rank empirical quantiles, 86 observed capital centroids; no diplomatic input',
                   'distance_quantiles': {str(q): observed[int((len(observed)-1)*q)] for q in (.01,.025,.05,.1,.2,.25,.5,.75,.9)},
                   'factions': len(starts), 'resolved_capitals': sum(f['centroid_x'] is not None for f in starts),
                   'region_graph_nodes': len(graph), 'region_graph_edges': sum(map(len,graph.values()))//2,
                   'strategic_node_count': len(nodes), 'strategic_link_count': len(links),
                   'strategic_networks': sorted({n['network_key'] for n in nodes if n['network_key']}),
                   'freeze': 'v2: 100-unit Regional, 150-unit Extended; Extended shared theater AND (hops <= 6 OR distance <= 75); topology correction for isolated raster regions, not diplomacy-dependent tuning'}
    return starts, pairs, calibration
