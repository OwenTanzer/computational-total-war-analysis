import copy
import json
import os
from pathlib import Path
import tempfile
import unittest

from ctw_analysis.coop_diplomacy import classify as diplomacy
from ctw_analysis.coop_geography import classify, distances
from ctw_analysis.coop_pairings import generate, open_atlas, verify_source, validate, GENERATED_FILES, ROOT


def faction(key, race):
    return {'faction_key':key,'race_slug':race}


class GeographyTests(unittest.TestCase):
    def test_missing_geometry_cannot_be_promoted_by_province(self):
        self.assertEqual(classify(None,0,True,True,True),('Unresolved',False,'Capital/start geometry unavailable'))

    def test_disconnected_is_not_zero_hops(self):
        self.assertIsNone(distances({'a':set(),'b':set()},'a').get('b'))
        self.assertEqual(distances({'a':{'b'},'b':{'a'}},'a')['b'],1)

    def test_close_but_cross_theater_island_does_not_invent_sea_route(self):
        self.assertFalse(classify(60,None,False,False,False)[1])

    def test_isolated_same_theater_start_can_qualify_without_claiming_path(self):
        self.assertEqual(classify(60,None,False,False,True)[:2],('Extended',True))
        self.assertEqual(classify(76,None,False,False,True)[:2],('Extended',False))

    def test_extended_requires_both_theater_and_bounded_separation(self):
        self.assertEqual(classify(149,6,False,False,True)[:2],('Extended',True))
        self.assertFalse(classify(149,7,False,False,True)[1])
        self.assertFalse(classify(149,6,False,False,False)[1])
        self.assertEqual(classify(151,2,False,True,True)[0],'Distant')


class DiplomacyTests(unittest.TestCase):
    def pair(self,key,race,other,other_race,pressure=()):
        a,b = faction(key,race),faction(other,other_race)
        result = diplomacy(a,b,pressure)
        self.assertEqual(result,diplomacy(b,a,pressure),'Classification must be symmetric')
        return result

    def test_wulfhart_teammate_exception_does_not_spread_to_repanse(self):
        r=self.pair('wh2_dlc13_emp_the_huntmarshals_expedition','empire','itza','lizardmen')
        self.assertEqual(r['diplomatic_class'],'Special')
        self.assertFalse(r['treaty_eligibility_unresolved'])
        r=self.pair('wh2_dlc14_brt_chevaliers_de_lyonesse','bretonnia','khemri','tomb_kings')
        self.assertEqual(r['diplomatic_class'],'Conflict')

    def test_arkhan_is_not_generic_tomb_king(self):
        for race,expected in [('tomb_kings','Conflict'),('vampire_counts','Clean'),('empire','Conflict')]:
            self.assertEqual(self.pair('wh2_dlc09_tmb_followers_of_nagash','tomb_kings','other',race)['diplomatic_class'],expected)

    def test_azazel_and_kemmler_have_scoped_bridges(self):
        self.assertEqual(self.pair('wh3_dlc20_chs_azazel','warriors_of_chaos','karl','empire')['diplomatic_class'],'Workable')
        self.assertEqual(self.pair('ordinary','warriors_of_chaos','karl','empire')['diplomatic_class'],'Conflict')
        r=self.pair('wh2_dlc11_vmp_the_barrow_legion','vampire_counts','nor','norsca')
        self.assertIn('kemmler_chaos',r['evidence_ids'])
        r=self.pair('wh2_dlc11_vmp_the_barrow_legion','vampire_counts','nur','nurgle')
        self.assertNotIn('kemmler_chaos',r['evidence_ids'])

    def test_marked_chaos_rivalry_overrides_same_race(self):
        self.assertEqual(self.pair('wh3_dlc20_chs_valkia','warriors_of_chaos','wh3_dlc20_chs_azazel','warriors_of_chaos')['diplomatic_class'],'Conflict')

    def test_no_unproven_golgfag_or_beastmen_team_override(self):
        for key,race in [('wh3_dlc26_ogr_golgfag','ogre_kingdoms'),('taurox','beastmen')]:
            r=self.pair(key,race,'other','ogre_kingdoms')
            self.assertEqual(r['diplomatic_class'],'Special')
            self.assertTrue(r['treaty_eligibility_unresolved'])

    def test_single_player_objective_is_not_a_multiplayer_war_lock(self):
        r=self.pair('a','empire','b','empire',['a:short:001:DESTROY_FACTION'])
        self.assertEqual(r['diplomatic_class'],'Workable')
        self.assertIn('single-player',r['analytical_inference'])

    def test_eshin_and_shared_multiplayer_rewards_have_friction(self):
        for key,race in [('wh2_main_skv_clan_eshin','skaven'),('a','wood_elves'),('a','tomb_kings'),('a','chaos_dwarfs')]:
            self.assertEqual(self.pair(key,race,'b',race)['diplomatic_class'],'Workable')


@unittest.skipUnless(os.environ.get('CTW_TEST_ROOT'),'Set CTW_TEST_ROOT to the locked source checkout for integration checks')
class LockedAtlasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=Path(os.environ['CTW_TEST_ROOT'])
        cls.tmp=tempfile.TemporaryDirectory()
        cls.output=Path(cls.tmp.name)/'study'
        cls.work=Path(cls.tmp.name)/'work'
        cls.report=generate(cls.root,cls.output,cls.work)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_universe_and_explicit_source_discrepancy(self):
        self.assertEqual(self.report['pair_count'],5356)
        self.assertEqual(len(self.report['missing_start_factions']),18)
        self.assertEqual(self.report['proximity_counts']['Unresolved'],1701)
        self.assertFalse(self.report['acceptance_complete'])

    def test_real_ulthuan_raster_hole(self):
        with open_atlas(self.root) as db:
            region='wh3_main_combi_region_gaean_vale'
            self.assertEqual(db.execute('select count(*) from region_adjacency where region_a=? or region_b=?',(region,region)).fetchone()[0],0)

    def test_actual_stale_pair_and_baseline_incompleteness(self):
        r=json.loads((self.output/'baseline_comparison.json').read_text())
        self.assertFalse(r['complete_pair_level_comparison'])
        self.assertEqual(r['missing_pair_rows'],123)
        self.assertEqual(r['recovered_row_result']['proximity_class'],'Distant')
        self.assertAlmostEqual(r['recovered_row_result']['centroid_distance'],267.842831,places=5)

    def test_regeneration_bytes(self):
        output,work=Path(self.tmp.name)/'second',Path(self.tmp.name)/'second_work'
        generate(self.root,output,work)
        for name in GENERATED_FILES:
            self.assertEqual((self.output/name).read_bytes(),(output/name).read_bytes(),name)
        self.assertEqual((self.work/'all_pairs.csv').read_bytes(),(work/'all_pairs.csv').read_bytes())

    def test_wrong_commit_lock_rejected_before_query(self):
        lock=json.loads((ROOT/'source_lock.json').read_text())
        lock['git_commit']='0'*40
        path=Path(self.tmp.name)/'bad_lock.json'
        path.write_text(json.dumps(lock))
        with self.assertRaisesRegex(ValueError,'HEAD differs'):
            verify_source(self.root,path)


class ValidationTests(unittest.TestCase):
    def test_duplicate_pair_rejected(self):
        # A plausible complete-sized universe with a duplicate must fail even if
        # the expected cardinality alone passes.
        from itertools import combinations
        keys={f'{n:03}' for n in range(104)}
        rows=[{'faction_a_key':a,'faction_b_key':b,'proximity_class':'Distant','diplomatic_class':'Conflict',
               'evidence_ids':'source','analytical_inference':'prior','diplomatic_caveat':'unknown',
               'included':False,'geographic_envelope':False,'treaty_eligibility_unresolved':False,'exclusion_reason':'distance'} for a,b in combinations(sorted(keys),2)]
        validate(rows,keys)
        rows[-1]=copy.deepcopy(rows[0])
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            validate(rows,keys)


if __name__=='__main__':
    unittest.main()
