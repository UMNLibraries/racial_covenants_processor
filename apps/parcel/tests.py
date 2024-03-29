from django.test import TestCase
from apps.zoon.models import ZooniverseSubject

from apps.parcel.utils.parcel_utils import standardize_addition, get_blocks, get_lots, write_join_strings


class JoinStringTests(TestCase):
    fixtures = ['plat', 'zoon']

    def test_standardize_addition_basic(self):
        for example in [
            "Jane's Addition",
            "Jane's Addition to the City of Minneapolis",
            "Jane's Addn",
            "Jane's Add'n",
        ]:
            self.assertEquals(standardize_addition(example), 'janes')

    def test_standardize_addition_2nd(self):
        for example in [
            "Jane's 2nd Addition",
            "Jane's 2nd Addition to the City of Minneapolis",
            "Jane's 2nd Addn",
            "Jane's 2nd Add'n",
            "Jane's 2nd Add",
            # FOREST PARK 2ND ADD
        ]:
            self.assertEquals(standardize_addition(example), 'janes 2nd')


    def test_standardize_addition_negatives(self):
        '''Things the standardizer should NOT standardize'''
        self.assertEquals(standardize_addition("Jane's Addiction"), 'janes addiction')
        self.assertEquals(standardize_addition("Jane's caddbury"), 'janes caddbury')
        self.assertEquals(standardize_addition("Jane's dfAddn"), 'janes dfaddn')
        self.assertEquals(standardize_addition("Jane's Add It Up"), 'janes add it up')  # Not sure I want this, may reconsider

    def test_standardize_addition_subdivision(self):
        for example in [
            'Another Subdivision',
            'Another SUBD.',
            'Another SUB'
        ]:
            self.assertEquals(standardize_addition(example), 'another')

    def test_standardize_addition_resubdivision(self):
        for example in [
            'Resubdivision of blocks 1, 2, 3 in Summit Park',
            'Re-subdivision of blocks 1, 2, 3 in Summit Park',
            'Re-subdivision of blocks 1 2 3 in Summit Park',
            'RESUBD of blocks 1 2 3 in Summit Park',
            'RESUB of blocks 1 2 3 in Summit Park',
            'RE-SUB of blocks 1 2 3 in Summit Park',
        ]:
            self.assertEquals(standardize_addition(example), 'resubdivision of blocks 1 2 3 in summit park')

    def test_write_join_strings_with_no_2(self):
        addition = "arden hills no. 2"
        block = '7'
        lot = '1'
        self.assertEquals(write_join_strings(
            addition, block, lot)[0]['join_string'], 'arden hills 2 block 7 lot 1')
        
    def test_get_blocks_none_text(self):
        """Does get_blocks give expected output for 'none' as entry?"""
        s = ZooniverseSubject.objects.get(pk=1)
        block, block_meta = get_blocks(s.block_final)
        self.assertEquals(block, "none")

    def test_get_blocks_none_nonsense(self):
        """Does get_blocks give expected output for 'nonsense' as entry?"""
        s = ZooniverseSubject.objects.get(pk=2)
        block, block_meta = get_blocks(s.block_final)
        self.assertEquals(block, 'nonsense')

    def test_get_blocks_none_null(self):
        """Does get_blocks give expected output for None as 'none'?"""
        block, block_meta = get_blocks(None)
        self.assertEquals(block, 'none')

    def test_lot_range(self):
        """Does get_lots render '1-20' as list [1,2,3,...20]"""
        lots, lots_meta = get_lots("1-20")
        self.assertEquals(lots, list(range(1,21)))

    def test_lot_bad_range_start(self):
        """Does get_lots render 'x1-20' None"""
        lots, lots_meta = get_lots("x1-20")
        self.assertEquals(lots, None)

    def test_lot_bad_range_end(self):
        """Does get_lots render '1-20x' as None"""
        lots, lots_meta = get_lots("1-20x")
        self.assertEquals(lots, None)

    def test_lot_bad_range_letter(self):
        """Does get_lots render '1x-20' as None"""
        lots, lots_meta = get_lots("1x-20")
        self.assertEquals(lots, None)

    def test_lot_simple_multi(self):
        """Does get_lots render 'LOTS 24 & 25 & 26' as ['24', '25', '26']"""
        lots, lots_meta = get_lots("LOTS 24 & 25 & 26")
        self.assertEquals(lots, ['24', '25', '26'])

    def test_lot_simple_multi_2(self):
        """Does get_lots render '24 & 25 & 26' as ['24', '25', '26']"""
        lots, lots_meta = get_lots("24 & 25 & 26")
        self.assertEquals(lots, ['24', '25', '26'])

    def test_lot_simple_multi_3(self):
        """Does get_lots render '24 & 25 & 26 AND SOME OTHER STUFF' as None"""
        lots, lots_meta = get_lots("LOT 24 & 25 & 26 AND SOME OTHER STUFF")
        self.assertEquals(lots, ['24', '25', '26'])

    def test_lot_simple_multi_4(self):
        """Does get_lots render 'East 20 feet of LOT 24 & 25 & 26' as None"""
        lots, lots_meta = get_lots("East 20 feet of LOT 24 & E 20 FT OF LOT 10")
        self.assertEquals(lots, None)

    def test_write_join_strings_basic(self):
        addition = "JANE'S ADDITION"
        block = '1'
        lot = '1'
        self.assertEquals(write_join_strings(
            addition, block, lot)[0]['join_string'], 'janes block 1 lot 1')

    def test_write_join_strings_multi(self):
        addition = "JANE'S ADDITION"
        block = '1'
        lot = '1,2'
        candidates = write_join_strings(addition, block, lot)
        join_strings = "; ".join([c['join_string'] for c in candidates])
        self.assertEquals(
            join_strings, 'janes block 1 lot 1; janes block 1 lot 2')
        
    def test_write_join_strings_with_no(self):
        addition = "ARDEN HILLS NO. 2"
        block = '7'
        lot = '1'
        self.assertEquals(write_join_strings(
            addition, block, lot)[0]['join_string'], 'arden hills 2 block 7 lot 1')
        
    def test_write_join_strings_with_no_2(self):
        addition = "arden hills no. 2"
        block = '7'
        lot = '1'
        self.assertEquals(write_join_strings(
            addition, block, lot)[0]['join_string'], 'arden hills 2 block 7 lot 1')
