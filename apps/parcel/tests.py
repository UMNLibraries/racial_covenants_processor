from django.test import TestCase
from apps.zoon.models import ZooniverseSubject

from apps.parcel.utils.parcel_utils import get_blocks, write_join_strings


class PlatTests(TestCase):
    fixtures = ['plat', 'zoon']

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
