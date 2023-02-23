from django.test import TestCase
from .models import Plat

from apps.parcel.utils.parcel_utils import standardize_addition


class PlatTests(TestCase):
    fixtures = ['plat', 'zoon']

    def test_standardize_addition(self):
        """Does standardize_addition give expected output?"""
        s = Plat.objects.get(plat_name="F. AMB'S ADDITION TO WEST ST. PAUL")
        self.assertEquals(standardize_addition(s.plat_name), "f ambs")

    def test_plat_name_standardized(self):
        """Does plat_name_standardized match output of standardize_addition?"""
        s = Plat.objects.get(plat_name="F. AMB'S ADDITION TO WEST ST. PAUL")
        print(standardize_addition(s.plat_name))
        self.assertEquals(s.plat_name_standardized,
                          standardize_addition(s.plat_name))

    #TODO: tests for plat extra addition candidates
