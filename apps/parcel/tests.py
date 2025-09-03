from django.test import TestCase, override_settings
from django.core import management
from apps.zoon.models import ZooniverseWorkflow, ZooniverseSubject, ManualCovenant
from apps.parcel.models import Parcel, ManualParcelCandidate, CovenantedParcel

from apps.parcel.utils.parcel_utils import standardize_addition, get_blocks, get_lots, write_join_strings
from apps.parcel.utils.export_utils import delete_flat_covenanted_parcels, save_flat_covenanted_parcels


class JoinStringTests(TestCase):
    fixtures = ['plat', 'zoon']

    def test_standardize_addition_basic(self):
        for example in [
            "Jane's Addition",
            "Janes' Addition",
            "Jane’s Addition",
            "Janes’ Addition",
            "Jane's Addition to the City of Minneapolis",
            "Jane's Addn",
            "Jane's Add'n",
        ]:
            self.assertEqual(standardize_addition(example), 'janes')

    def test_standardize_addition_weird_1st(self):
        '''Leave these (mostly) alone, these are not additions to CITIES'''

        self.assertEqual(standardize_addition("1st Addition To Eskesens Lots"), "1st to eskesens lots")
        self.assertEqual(standardize_addition("2nd Addition To Eskesens Lots"), "2nd to eskesens lots")
        self.assertEqual(standardize_addition("1st Addition To Maple Ridge Estates"), "1st to maple ridge estates")
        self.assertEqual(standardize_addition("3rd Addition To Maple Ridge Estates"), "3rd to maple ridge estates")
        self.assertEqual(standardize_addition("Fourth Addition To Maple Ridge Estates"), "4th to maple ridge estates")
        self.assertEqual(standardize_addition("First Addition To Maple Ridge Estates"), "1st to maple ridge estates")
        self.assertEqual(standardize_addition("1st Addition to Jane's"), "1st to janes")
        self.assertEqual(standardize_addition("10th Addition To Breezy Point Estates"), "10th to breezy point estates")

    def test_standardize_addition_2nd(self):
        for example in [
            "Jane's 2nd Addition",
            "Jane's 2nd Addition to the City of Minneapolis",
            "Jane's 2nd Addn",
            "Jane's 2nd Add'n",
            "Jane's 2nd Add",
            # FOREST PARK 2ND ADD
        ]:
            self.assertEqual(standardize_addition(example), 'janes 2nd')


    def test_standardize_addition_negatives(self):
        '''Things the standardizer should NOT standardize'''
        self.assertEqual(standardize_addition("Jane's Addiction"), 'janes addiction')
        self.assertEqual(standardize_addition("Jane's caddbury"), 'janes caddbury')
        self.assertEqual(standardize_addition("Jane's dfAddn"), 'janes dfaddn')
        self.assertEqual(standardize_addition("Jane's Add It Up"), 'janes add it up')  # Not sure I want this, may reconsider

    def test_standardize_addition_subdivision(self):
        for example in [
            'Another Subdivision',
            'Another SUBD.',
            'Another SUB'
        ]:
            self.assertEqual(standardize_addition(example), 'another')

    def test_standardize_addition_resubdivision(self):
        for example in [
            'Resubdivision of blocks 1, 2, 3 in Summit Park',
            'Re-subdivision of blocks 1, 2, 3 in Summit Park',
            'Re-subdivision of blocks 1 2 3 in Summit Park',
            'RESUBD of blocks 1 2 3 in Summit Park',
            'RESUB of blocks 1 2 3 in Summit Park',
            'RE-SUB of blocks 1 2 3 in Summit Park',
        ]:
            self.assertEqual(standardize_addition(example), 'resubdivision of blocks 1 2 3 in summit park')

    def test_write_join_strings_with_no_2(self):
        addition = "arden hills no. 2"
        block = '7'
        lot = '1'
        self.assertEqual(write_join_strings(
            addition, block, lot)[0]['join_string'], 'arden hills 2 block 7 lot 1')
        
    def test_get_blocks_none_text(self):
        """Does get_blocks give expected output for 'none' as entry?"""
        s = ZooniverseSubject.objects.get(pk=1)
        block, block_meta = get_blocks(s.block_final)
        self.assertEqual(block, "none")

    def test_get_blocks_none_nonsense(self):
        """Does get_blocks give expected output for 'nonsense' as entry?"""
        s = ZooniverseSubject.objects.get(pk=2)
        block, block_meta = get_blocks(s.block_final)
        self.assertEqual(block, 'nonsense')

    def test_get_blocks_none_null(self):
        """Does get_blocks give expected output for None as 'none'?"""
        block, block_meta = get_blocks(None)
        self.assertEqual(block, 'none')

    def test_lot_range(self):
        """Does get_lots render '1-20' as list [1,2,3,...20]"""
        lots, lots_meta = get_lots("1-20")
        self.assertEqual(lots, [str(x) for x in list(range(1,21))])

    def test_lot_range_thru(self):
        """Does get_lots render 'LOTS 2525 THRU 2529' as list [2525,2526,...2529]"""
        lots, lots_meta = get_lots("LOTS 2525 THRU 2529")
        self.assertEqual(lots, ['2525', '2526', '2527', '2528', '2529'])

    def test_lot_bad_range_start(self):
        """Does get_lots render 'x1-20' None"""
        lots, lots_meta = get_lots("x1-20")
        self.assertEqual(lots, None)

    def test_lot_bad_range_end(self):
        """Does get_lots render '1-20x' as None"""
        lots, lots_meta = get_lots("1-20x")
        self.assertEqual(lots, None)

    def test_lot_bad_range_letter(self):
        """Does get_lots render '1x-20' as None"""
        lots, lots_meta = get_lots("1x-20")
        self.assertEqual(lots, None)

    def test_lot_simple_multi(self):
        """Does get_lots render 'LOTS 24 & 25 & 26' as ['24', '25', '26']"""
        lots, lots_meta = get_lots("LOTS 24 & 25 & 26")
        self.assertEqual(lots, ['24', '25', '26'])

    def test_lot_simple_multi_2(self):
        """Does get_lots render '24 & 25 & 26' as ['24', '25', '26']"""
        lots, lots_meta = get_lots("24 & 25 & 26")
        self.assertEqual(lots, ['24', '25', '26'])

    def test_lot_simple_multi_3(self):
        """Does get_lots render '24 & 25 & 26 AND SOME OTHER STUFF' as None"""
        lots, lots_meta = get_lots("LOT 24 & 25 & 26 AND SOME OTHER STUFF")
        self.assertEqual(lots, None)

    def test_lot_simple_multi_4(self):
        """Does get_lots render 'East 20 feet of LOT 24 & 25 & 26' as None"""
        lots, lots_meta = get_lots("East 20 feet of LOT 24 & E 20 FT OF LOT 10")
        self.assertEqual(lots, None)

    def test_lot_simple_multi_5(self):
        """Does get_lots render '2768, 2769, 2770, 2771, and 2772' as ['2768', '2769', '2770', '2771', '2772']"""
        lots, lots_meta = get_lots("2768, 2769, 2770, 2771, and 2772")
        
        self.assertEqual(lots, ['2768', '2769', '2770', '2771', '2772'])

    def test_lot_simple_multi_6(self):
        """Does get_lots render 'LOTS 5001, 5002, 5003, 5004, 5005, & 5006' as ['5001', '5002', '5003', '5004', '5005', '5006']"""
        lots, lots_meta = get_lots("LOTS 5001, 5002, 5003, 5004, 5005, & 5006")
        
        self.assertEqual(lots, ['5001', '5002', '5003', '5004', '5005', '5006'])

    def test_lots_1_and_2(self):
        '''Do "lots 1 and 2" return 1 and 2'''
        lots, lots_meta = get_lots("lots 1 and 2")
        print("test_lots_1_and_2: " + lots_meta)
        self.assertEqual(lots, ['1', '2'])

    def test_lot_leading_zero(self):
        '''Do leading zeroes get removed from lots, e.g. 001 should be 1'''
        lots, lots_meta = get_lots("001")
        self.assertEqual(lots, ['1'])

    def test_lot_leading_zero_list(self):
        '''Do leading zeroes get removed from lots, e.g. 001 should be 1'''
        lots, lots_meta = get_lots("Lot 024 & 01")
        self.assertEqual(lots, ['1', '24'])

    def test_lot_fake_leading_zero(self):
        '''Do leading zeroes after another digit get ignored, e.g. 1001 should be 1001'''
        lots, lots_meta = get_lots("1001")
        self.assertEqual(lots, ['1001'])

    def test_lot_single_letter(self):
        '''Lot parsing of single-letter lots (e.g. Lot A, Lot B)'''
        lots, lots_meta = get_lots("Lot A")
        self.assertEqual(lots, ['a'])

        lots, lots_meta = get_lots("Lot B")
        self.assertEqual(lots, ['b'])

    def test_lot_with_por(self):
        '''Lot parsing of a full lot with a partial lot added on, e.g. Contra Costa County'''
        lots, lots_meta = get_lots("LOT 13 POR 12")
        self.assertEqual(lots, ['13'])

    def test_block_leading_zero(self):
        '''Do leading zeroes get removed from blocks, e.g. 001 should be 1'''
        blocks, blocks_meta = get_blocks("001")
        self.assertEqual(blocks, '1')

    def test_block_fake_leading_zero(self):
        '''Do leading zeroes after another digit get ignored, e.g. 1001 should be 1001'''
        blocks, blocks_meta = get_blocks("1001")
        self.assertEqual(blocks, '1001')

    def test_block_blk(self):
        blocks, blocks_meta = get_blocks("BLK 55")
        self.assertEqual(blocks, '55')
        blocks, blocks_meta = get_blocks("BLOCK 55")
        self.assertEqual(blocks, '55')

    def test_write_join_strings_basic(self):
        addition = "JANE'S ADDITION"
        block = '1'
        lot = '1'
        self.assertEqual(write_join_strings(
            addition, block, lot)[0]['join_string'], 'janes block 1 lot 1')

    def test_write_join_strings_multi(self):
        addition = "JANE'S ADDITION"
        block = '1'
        lot = '1,2'
        candidates = write_join_strings(addition, block, lot)
        join_strings = "; ".join([c['join_string'] for c in candidates])
        self.assertEqual(
            join_strings, 'janes block 1 lot 1; janes block 1 lot 2')
        
    def test_write_join_strings_with_no(self):
        addition = "ARDEN HILLS NO. 2"
        block = '7'
        lot = '1'
        self.assertEqual(write_join_strings(
            addition, block, lot)[0]['join_string'], 'arden hills 2 block 7 lot 1')
        
    def test_write_join_strings_with_no_2(self):
        addition = "arden hills no. 2"
        block = '7'
        lot = '1'
        self.assertEqual(write_join_strings(
            addition, block, lot)[0]['join_string'], 'arden hills 2 block 7 lot 1')

TEST_ZOON_SETTINGS = {
    'MN Test County': {
        'zoon_workflow_id': 13143,
        'zoon_workflow_version': 4.1,
    }
}

@override_settings(ZOONIVERSE_QUESTION_LOOKUP=TEST_ZOON_SETTINGS)
class ParcelCandidateTests(TestCase):
    fixtures = ['zoon', 'plat', 'parcel']

    @classmethod
    def setUpTestData(cls):
        workflow = ZooniverseWorkflow.objects.get(pk=1)
        
        # Rebuild spatial lookups and run parcel auto-match before running these tests
        management.call_command('rebuild_parcel_spatial_lookups', workflow=workflow.workflow_name)

    def test_manualparcelcandidate_on_rebuild(self):
        '''After rebuild spatial lookups, has a ParcelJoinCandidate successfully been created from ManualParcelCandidate pk 1?'''
        parcel = Parcel.objects.get(workflow_id=1, pk=9)
        self.assertEqual(parcel.parceljoincandidate_set.all().count(), 2)
        self.assertEqual(parcel.parceljoincandidate_set.filter(join_string='mpc base block 1 lot 6').count(), 1)

    def test_manualparcelcandidate_save(self):
        '''Does creating a ManualParcelCandidate generate an additional ParcelJoinCandidate? And does deleting the MPC remove it from join candidates?'''
        parcel = Parcel.objects.get(workflow_id=1, pk=8)

        self.assertEqual(parcel.parceljoincandidate_set.all().count(), 1)

        mpc = ManualParcelCandidate(
            workflow_id=1,
            parcel=parcel,
            addition='New Addition',
            block='1',
            lot='1',
            comments="Let's add an MPC"
        )
        mpc.save()

        for pjc in parcel.parceljoincandidate_set.all().values():
            print(pjc)

        self.assertEqual(parcel.parceljoincandidate_set.all().count(), 2)
        self.assertEqual(parcel.parceljoincandidate_set.filter(join_string='new block 1 lot 1').count(), 1)

        mpc.delete()
        self.assertEqual(parcel.parceljoincandidate_set.all().count(), 1)


@override_settings(ZOONIVERSE_QUESTION_LOOKUP=TEST_ZOON_SETTINGS)
class CovenantedParcelTests(TestCase):
    fixtures = ['zoon', 'plat', 'parcel']

    @classmethod
    def setUpTestData(cls):
        workflow = ZooniverseWorkflow.objects.get(pk=1)
        
        # Rebuild spatial lookups and run parcel auto-match before running these tests
        management.call_command('rebuild_parcel_spatial_lookups', workflow=workflow.workflow_name)
        management.call_command('rebuild_covenant_spatial_lookups', workflow=workflow.workflow_name)
        management.call_command('match_parcels', workflow=workflow.workflow_name)

    def test_parcel_match(self):
        parcel_1 = Parcel.objects.get(pin_primary='covenanted-parcel-1')
        self.assertEqual(parcel_1.bool_covenant, True)

        parcel_2 = Parcel.objects.get(pin_primary='covenanted-parcel-2')
        self.assertEqual(parcel_2.bool_covenant, True)

    def test_save_flat_covenanted_parcels(self):

        parcels = Parcel.objects.filter(pin_primary__in=['covenanted-parcel-1', 'covenanted-parcel-2'])

        # Delete covs created by match_parcels
        cleared_parcels = delete_flat_covenanted_parcels(parcels)
        self.assertEqual(CovenantedParcel.objects.filter(parcel__pin_primary='covenanted-parcel-1').count(), 0)
        self.assertEqual(CovenantedParcel.objects.filter(parcel__pin_primary='covenanted-parcel-2').count(), 0)

        # Manually create some new covs
        flat_covs = save_flat_covenanted_parcels(parcels)
        self.assertEqual(CovenantedParcel.objects.filter(parcel__pin_primary='covenanted-parcel-1').count(), 1)
        self.assertEqual(CovenantedParcel.objects.filter(parcel__pin_primary='covenanted-parcel-2').count(), 1)

        flat_cov_1 = flat_covs.get(parcel__pin_primary='covenanted-parcel-1')
        self.assertEqual(flat_cov_1.cov_text, 'This is sample covenant text')

        # Delete manually created covs and test again
        cleared_parcels = delete_flat_covenanted_parcels(parcels)
        self.assertEqual(CovenantedParcel.objects.filter(parcel__pin_primary='covenanted-parcel-1').count(), 0)
        self.assertEqual(CovenantedParcel.objects.filter(parcel__pin_primary='covenanted-parcel-2').count(), 0)

    def test_addition_wide_covenanted_parcel_creation(self):
        # Create addition-wide ZooniverseSubject and see if it creates CovenantedParcel objects
        cps_initial = CovenantedParcel.objects.filter(
            add_cov='Covenanted Parcel AW Addition'
        )
        self.assertEqual(cps_initial.count(), 0)

        awc = ZooniverseSubject(
            workflow_id=1,
            bool_covenant=True,
            # bool_covenant_final=True,
            bool_parcel_match=False,
            deed_date_final='2025-04-01',
            addition='Not Covenanted Parcel AW Addition',
            addition_final='Not Covenanted Parcel AW Addition',
            block='NONE',
            lot='NONE',
            match_type='AW',
            match_type_final='AW',
            zoon_subject_id='1234',
            image_ids='',
        )
        awc.save()

        awc2 = ZooniverseSubject.objects.get(addition='Not Covenanted Parcel AW Addition')
        awc2.save()

        cps_after = CovenantedParcel.objects.filter(
            add_cov='Not Covenanted Parcel AW Addition'
        )
        
        self.assertEqual(cps_after.count(), 2)

    def test_manual_covenant_covenanted_parcel_creation(self):
        # TODO: ManualCovenant testing for CovenantParcel creation
        cps_initial = CovenantedParcel.objects.filter(
            add_cov='Manual Covenant CP Addition'
        )
        self.assertEqual(cps_initial.count(), 0)

        mc = ManualCovenant(
            workflow_id=1,
            bool_confirmed=True,
            bool_parcel_match=False,
            deed_date='2025-04-01',
            addition='Manual Covenant CP Addition',
            block='1',
            lot='1'
        )
        mc.save()

        mc2 = ManualCovenant.objects.get(addition='Manual Covenant CP Addition')
        mc2.save()

        cps_after = CovenantedParcel.objects.filter(
            add_cov='Manual Covenant CP Addition'
        )
        
        self.assertEqual(cps_after.count(), 1)

        # Now delete the ManualCovenant and confirm that the ManualCovenant is deleted
        mc2.delete()

        cps_after_delete = CovenantedParcel.objects.filter(
            add_cov='Manual Covenant CP Addition'
        )
        self.assertEqual(cps_after_delete.count(), 0)

