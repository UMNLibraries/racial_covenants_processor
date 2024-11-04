from django.test import TestCase
from django.core.management import call_command

from .models import Plat, SubdivisionAlternateName
from apps.parcel.models import Parcel
from apps.zoon.models import ZooniverseSubject, ZooniverseWorkflow

from apps.parcel.utils.parcel_utils import standardize_addition


class PlatTests(TestCase):
    fixtures = ['plat', 'zoon', 'parcel']

    # @classmethod
    # def setUpClass(self):
        

    def test_standardize_addition(self):
        """Does standardize_addition give expected output?"""
        s = Plat.objects.get(plat_name="F. AMB'S ADDITION TO WEST ST. PAUL")
        self.assertEquals(standardize_addition(s.plat_name), "f ambs")

    def test_standardize_addition_2(self):
        """Does standardize_addition give expected output?"""
        self.assertEquals(standardize_addition('ARDEN HILLS NO. 2'), "arden hills 2")

    def test_plat_name_standardized(self):
        """Does plat_name_standardized match output of standardize_addition?"""
        s = Plat.objects.get(plat_name="F. AMB'S ADDITION TO WEST ST. PAUL")
        print(standardize_addition(s.plat_name))
        self.assertEquals(s.plat_name_standardized,
                          standardize_addition(s.plat_name))
        
    def test_subdivision_parcel_match(self):
        """Does an addition-wide covenant match all parcels in a subdivision"""

        workflow = ZooniverseWorkflow.objects.get(pk=1)

        # Set up database first time
        TEST_ZOON_SETTINGS = {
            workflow.workflow_name: {
                'zoon_workflow_id': workflow.zoon_id,
                'zoon_workflow_version': workflow.version,
            }
        }

        with self.settings(ZOONIVERSE_QUESTION_LOOKUP=TEST_ZOON_SETTINGS):
            call_command("rebuild_parcel_spatial_lookups", workflow='MN Test County')
            call_command("rebuild_covenant_spatial_lookups", workflow='MN Test County')
            call_command("match_parcels", '--test', workflow='MN Test County')

        parcels_to_match = Parcel.objects.filter(workflow=1, plat_name='LYNDALE BEACH 2ND ADDN')
        parcels_count = parcels_to_match.count()
        self.assertGreater(parcels_count, 1)

        zoon_to_match = ZooniverseSubject.objects.get(
            workflow_id=1,
            addition_final='Lyndale Beach 2nd Addition',
            match_type_final='AW'
        )

        for parcel in parcels_to_match:
            if parcel.zooniversesubject_set.filter(pk=zoon_to_match.pk).count() == 1:
                parcels_count -= 1

        self.assertEqual(parcels_count, 0)

    def test_subdivision_alternate_parcel_match(self):
        """Does an addition-wide covenant match all parcels in a subdivision with alternate name"""

        parcels_to_match = Parcel.objects.filter(workflow=1, plat_name='LYNDALE BEACH 2ND ADDN')
        parcels_count = parcels_to_match.count()
        self.assertGreater(parcels_count, 1)

        zoon_to_match = ZooniverseSubject.objects.get(
            workflow_id=1,
            addition_final='Lyndale Beach 2nd Addition Variation',
            match_type_final='AW'
        )

        # Now create SubdivisionAlternateName
        print('Creating new SubdivisionAlternateName')
        san = SubdivisionAlternateName.objects.create(
            workflow_id=1,
            subdivision_id=1,
            subdivision_name='LYNDALE BEACH 2ND ADDN',
            alternate_name='Lyndale Beach 2nd Addition Variation'
        )
        san.save()

        for parcel in parcels_to_match:
            if parcel.zooniversesubject_set.filter(pk=zoon_to_match.pk).count() == 1:
                parcels_count -= 1

        self.assertEqual(parcels_count, 0)
