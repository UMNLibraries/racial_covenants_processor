from django.test import TestCase, override_settings
from django.core import management

from apps.zoon.models import ZooniverseWorkflow, ZooniverseSubject, ManualCovenant, ManualParcelPINLink, ManualCovenantParcelPINLink
from apps.parcel.models import Parcel
from apps.deed.utils.deed_pagination import tag_prev_next_image_sql
from apps.zoon.utils.zooniverse_load import build_zooniverse_manifest
# from apps.zoon.management.commands import load_zooniverse_export
from apps.zoon.management.commands.load_zooniverse_export import Command as LoadZooniverseExportTest


class ZooniverseUploadTests(TestCase):
    fixtures = ['deed', 'zoon']

    @classmethod
    def setUpTestData(cls):
    # def setUp(self):
        # Set up database first time
        workflow = ZooniverseWorkflow.objects.get(pk=1)
        # In the initial state of the deed fixtures, the prev/next images aren't set, so you need to do that before testing exports
        tag_prev_next_image_sql(workflow, True)

    def test_pagination_page_2(self):
        """Does build_zooniverse_manifest generate correct image sequence?
        In this case, should be:
            default_frame: 2
            #image1: page_1
            #image2: page_2
            #image3: page_3
        """
        workflow = ZooniverseWorkflow.objects.get(pk=1)

        manifest_df = build_zooniverse_manifest(workflow, exclude_ids=[], num_rows=None)

        test_image_row = manifest_df[manifest_df['#s3_lookup'] == 'Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_NONE_book_140_page_2']

        self.assertEqual(test_image_row['default_frame'].iloc[0], 2)

        self.assertIn('web/fake/DEEDS/doc_NONE_book_140_page_1.jpg', test_image_row['#image1'].iloc[0])
        self.assertIn('web/fake/DEEDS/doc_NONE_book_140_page_2.jpg', test_image_row['#image2'].iloc[0])
        self.assertIn('web/fake/DEEDS/doc_NONE_book_140_page_3.jpg', test_image_row['#image3'].iloc[0])

    def test_pagination_page_none_splitpage(self):
        """Does build_zooniverse_manifest generate correct image sequence?
        In this case, should be:
            default_frame: 2
            #image1: SPLITPAGE_1
            #image2: SPLITPAGE_2
            #image3: SPLITPAGE_3
        """
        workflow = ZooniverseWorkflow.objects.get(pk=1)

        manifest_df = build_zooniverse_manifest(workflow, exclude_ids=[], num_rows=None)

        test_image_row = manifest_df[manifest_df['#s3_lookup'] == 'Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_NONE_book_140_page_NONE_SPLITPAGE_2']

        self.assertEqual(test_image_row['default_frame'].iloc[0], 2)

        self.assertIn('web/fake/DEEDS/NONE_SPLITPAGE_1.jpg', test_image_row['#image1'].iloc[0])
        self.assertIn('web/fake/DEEDS/NONE_SPLITPAGE_2.jpg', test_image_row['#image2'].iloc[0])
        self.assertIn('web/fake/DEEDS/NONE_SPLITPAGE_3.jpg', test_image_row['#image3'].iloc[0])

    def test_pagination_page_none_splitpage_1(self):
        """Does build_zooniverse_manifest generate correct image sequence?
        In this case, should be:
            default_frame: 1
            #image1: SPLITPAGE_1
            #image2: SPLITPAGE_2
            #image3: SPLITPAGE_3
        """
        workflow = ZooniverseWorkflow.objects.get(pk=1)

        manifest_df = build_zooniverse_manifest(workflow, exclude_ids=[], num_rows=None)

        test_image_row = manifest_df[manifest_df['#s3_lookup'] == 'Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_NONE_book_140_page_NONE_SPLITPAGE_1']

        self.assertEqual(test_image_row['default_frame'].iloc[0], 1)

        self.assertIn('web/fake/DEEDS/NONE_SPLITPAGE_1.jpg', test_image_row['#image1'].iloc[0])
        self.assertIn('web/fake/DEEDS/NONE_SPLITPAGE_2.jpg', test_image_row['#image2'].iloc[0])
        self.assertIn('web/fake/DEEDS/NONE_SPLITPAGE_3.jpg', test_image_row['#image3'].iloc[0])

    def test_pagination_page_none_splitpage_4(self):
        """Does build_zooniverse_manifest generate correct image sequence?
        In this case, should be:
            default_frame: 2
            #image1: SPLITPAGE_3
            #image2: SPLITPAGE_4
            #image3: ''
        """
        workflow = ZooniverseWorkflow.objects.get(pk=1)

        manifest_df = build_zooniverse_manifest(workflow, exclude_ids=[], num_rows=None)

        test_image_row = manifest_df[manifest_df['#s3_lookup'] == 'Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_NONE_book_140_page_NONE_SPLITPAGE_4']

        self.assertEqual(test_image_row['default_frame'].iloc[0], 2)

        self.assertIn('web/fake/DEEDS/NONE_SPLITPAGE_3.jpg', test_image_row['#image1'].iloc[0])
        self.assertIn('web/fake/DEEDS/NONE_SPLITPAGE_4.jpg', test_image_row['#image2'].iloc[0])
        self.assertEqual(test_image_row['#image3'].iloc[0], '')

    def test_pagination_page_n_splitpage_2(self):
        """Does build_zooniverse_manifest generate correct image sequence?
        In this case, should be:
            default_frame: 2
            #image1: page_n_SPLITPAGE_1
            #image2: page_n_SPLITPAGE_2
            #image3: page_n_SPLITPAGE_3
        """
        workflow = ZooniverseWorkflow.objects.get(pk=1)

        manifest_df = build_zooniverse_manifest(workflow, exclude_ids=[], num_rows=None)

        test_image_row = manifest_df[manifest_df['#s3_lookup'] == 'Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_NONE_book_140_page_200_SPLITPAGE_2']

        self.assertEqual(test_image_row['default_frame'].iloc[0], 2)

        self.assertIn('web/fake/DEEDS/doc_NONE_book_140_page_200_SPLITPAGE_1.jpg', test_image_row['#image1'].iloc[0])
        self.assertIn('web/fake/DEEDS/doc_NONE_book_140_page_200_SPLITPAGE_2.jpg', test_image_row['#image2'].iloc[0])
        self.assertIn('web/fake/DEEDS/doc_NONE_book_140_page_200_SPLITPAGE_3.jpg', test_image_row['#image3'].iloc[0])

    def test_pagination_page_n_splitpage_1(self):
        """Does build_zooniverse_manifest generate correct image sequence?
        In this case, should be:
            default_frame: 1
            #image1: page_n_SPLITPAGE_1
            #image2: page_n_SPLITPAGE_2
            #image3: page_n_SPLITPAGE_3
        """
        workflow = ZooniverseWorkflow.objects.get(pk=1)

        manifest_df = build_zooniverse_manifest(workflow, exclude_ids=[], num_rows=None)

        test_image_row = manifest_df[manifest_df['#s3_lookup'] == 'Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_NONE_book_140_page_200_SPLITPAGE_1']

        self.assertEqual(test_image_row['default_frame'].iloc[0], 1)

        self.assertIn('web/fake/DEEDS/doc_NONE_book_140_page_200_SPLITPAGE_1.jpg', test_image_row['#image1'].iloc[0])
        self.assertIn('web/fake/DEEDS/doc_NONE_book_140_page_200_SPLITPAGE_2.jpg', test_image_row['#image2'].iloc[0])
        self.assertIn('web/fake/DEEDS/doc_NONE_book_140_page_200_SPLITPAGE_3.jpg', test_image_row['#image3'].iloc[0])

    def test_pagination_page_n_splitpage_4(self):
        """Does build_zooniverse_manifest generate correct image sequence?
        In this case, should be:
            default_frame: 2
            #image1: page_n_SPLITPAGE_3
            #image2: page_n_SPLITPAGE_4
            #image3: ''
        """
        workflow = ZooniverseWorkflow.objects.get(pk=1)

        manifest_df = build_zooniverse_manifest(workflow, exclude_ids=[], num_rows=None)

        test_image_row = manifest_df[manifest_df['#s3_lookup'] == 'Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_NONE_book_140_page_200_SPLITPAGE_4']

        self.assertEqual(test_image_row['default_frame'].iloc[0], 2)

        self.assertIn('web/fake/DEEDS/doc_NONE_book_140_page_200_SPLITPAGE_3.jpg', test_image_row['#image1'].iloc[0])
        self.assertIn('web/fake/DEEDS/doc_NONE_book_140_page_200_SPLITPAGE_4.jpg', test_image_row['#image2'].iloc[0])
        self.assertEqual(test_image_row['#image3'].iloc[0], '')

    # Milwaukee examples
    def test_pagination_milw_doc_num_page_2_only_2(self):
        """Does build_zooniverse_manifest generate correct image sequence?
        In this case, should be:
            default_frame: 2
            #image1: 02806155_NOTINDEX_0001.jpg
            #image2: 02806155_NOTINDEX_0002.jpg
            #image3: ''
        """

        workflow = ZooniverseWorkflow.objects.get(pk=1)
        manifest_df = build_zooniverse_manifest(workflow, exclude_ids=[], num_rows=None)

        test_image_row = manifest_df[manifest_df['#s3_lookup'] == '30000102/02806155_NOTINDEX_0002']

        self.assertEqual(test_image_row['default_frame'].iloc[0], 2)

        self.assertIn('web/fake/30000102/02806155_NOTINDEX_0001.jpg', test_image_row['#image1'].iloc[0])
        self.assertIn('web/fake/30000102/02806155_NOTINDEX_0002.jpg', test_image_row['#image2'].iloc[0])
        self.assertEqual(test_image_row['#image3'].iloc[0], '')

    def test_pagination_milw_doc_num_page_2_of_3(self):
        """Does build_zooniverse_manifest generate correct image sequence?
        In this case, should be:
            default_frame: 2
            #image1: 02720303_NOTINDEX_0001.jpg
            #image2: 02720303_NOTINDEX_0002.jpg
            #image3: 02720303_NOTINDEX_0003.jpg
        """

        workflow = ZooniverseWorkflow.objects.get(pk=1)
        manifest_df = build_zooniverse_manifest(workflow, exclude_ids=[], num_rows=None)

        test_image_row = manifest_df[manifest_df['#s3_lookup'] == '30000102/02720303_NOTINDEX_0002']

        self.assertEqual(test_image_row['default_frame'].iloc[0], 2)

        self.assertIn('web/fake/30000102/02720303_NOTINDEX_0001.jpg', test_image_row['#image1'].iloc[0])
        self.assertIn('web/fake/30000102/02720303_NOTINDEX_0002.jpg', test_image_row['#image2'].iloc[0])
        self.assertIn('web/fake/30000102/02720303_NOTINDEX_0003.jpg', test_image_row['#image3'].iloc[0])

    def test_pagination_milw_doc_num_page_1_of_3(self):
        """Does build_zooniverse_manifest generate correct image sequence?
        In this case, should be:
            default_frame: 1
            #image1: 02720303_NOTINDEX_0001.jpg
            #image2: 02720303_NOTINDEX_0002.jpg
            #image3: 02720303_NOTINDEX_0003.jpg
        """

        workflow = ZooniverseWorkflow.objects.get(pk=1)
        manifest_df = build_zooniverse_manifest(workflow, exclude_ids=[], num_rows=None)

        test_image_row = manifest_df[manifest_df['#s3_lookup'] == '30000102/02720303_NOTINDEX_0001']

        self.assertEqual(test_image_row['default_frame'].iloc[0], 1)

        self.assertIn('web/fake/30000102/02720303_NOTINDEX_0001.jpg', test_image_row['#image1'].iloc[0])
        self.assertIn('web/fake/30000102/02720303_NOTINDEX_0002.jpg', test_image_row['#image2'].iloc[0])
        self.assertIn('web/fake/30000102/02720303_NOTINDEX_0003.jpg', test_image_row['#image3'].iloc[0])

    # Run this one last in this class
    def test_clear_all_tables(self):

        workflow = ZooniverseWorkflow.objects.get(pk=1)
        zs = ZooniverseSubject.objects.filter(workflow=workflow)
        self.assertGreater(zs.count(), 0)
        
        LoadZooniverseExportTest.clear_all_tables(None, workflow.workflow_name)

        zs = ZooniverseSubject.objects.filter(workflow=workflow)
        self.assertEqual(zs.count(), 0)


TEST_ZOON_SETTINGS = {
    'MN Test County': {
        'zoon_workflow_id': 13143,
        'zoon_workflow_version': 4.1,
    }
}

@override_settings(ZOONIVERSE_QUESTION_LOOKUP=TEST_ZOON_SETTINGS)
class ParcelMatchTests(TestCase):
    fixtures = ['parcel', 'zoon', 'plat']

    @classmethod
    def setUpTestData(cls):
    # def setUp(self):
        # Set up database first time
        workflow = ZooniverseWorkflow.objects.get(pk=1)

        # TEST_ZOON_SETTINGS = {
        #     workflow.workflow_name: {
        #         'zoon_workflow_id': workflow.zoon_id,
        #         'zoon_workflow_version': workflow.version,
        #     }
        # }
        
        # with cls.settings(ZOONIVERSE_QUESTION_LOOKUP=TEST_ZOON_SETTINGS):
        # Rebuild spatial lookups and run parcel auto-match before running these tests
        management.call_command('rebuild_parcel_spatial_lookups', workflow=workflow.workflow_name)
        management.call_command('rebuild_covenant_spatial_lookups', workflow=workflow.workflow_name)
        management.call_command('match_parcels', '--test', workflow=workflow.workflow_name)

    def test_parcel_match_zoon_1(self):
        parcel_lot_2 = Parcel.objects.get(workflow_id=1, plat_standardized='janes', block=1, lot=2)
        parcel_lot_3 = Parcel.objects.get(workflow_id=1, plat_standardized='janes', block=1, lot=3)

        zoon_lot_2_and_3 = ZooniverseSubject.objects.get(pk=5)

        self.assertEqual(parcel_lot_2.bool_covenant, True)
        self.assertEqual(parcel_lot_3.bool_covenant, True)
        self.assertIn(parcel_lot_2, zoon_lot_2_and_3.parcel_matches.all())
        self.assertIn(parcel_lot_3, zoon_lot_2_and_3.parcel_matches.all())

    def test_parcel_match_manual_1(self):
        parcel_lot_4 = Parcel.objects.get(workflow_id=1, plat_standardized='janes', block=1, lot=4)

        manual_lot_4 = ManualCovenant.objects.get(pk=1)

        self.assertEqual(parcel_lot_4.bool_covenant, True)
        self.assertIn(parcel_lot_4, manual_lot_4.parcel_matches.all())

    def test_parcel_match_manual_addition_wide_1(self):
        parcel_lot_6 = Parcel.objects.get(workflow_id=1, plat_standardized='many covenants 1st', block=1, lot=1)
        parcel_lot_7 = Parcel.objects.get(workflow_id=1, plat_standardized='many covenants 1st', block=2, lot=1)

        manual_add_wide = ManualCovenant.objects.get(pk=2)

        self.assertEqual(manual_add_wide.bool_parcel_match, True)
        self.assertEqual(parcel_lot_6.bool_covenant, True)
        self.assertEqual(parcel_lot_7.bool_covenant, True)
        self.assertIn(parcel_lot_6, manual_add_wide.parcel_matches.all())
        self.assertIn(parcel_lot_7, manual_add_wide.parcel_matches.all())

    def test_parcel_match_manual_parcel_pin_1(self):
        parcel_lot_10 = Parcel.objects.get(workflow_id=1, pin_primary='mppl-test-pin-1')

        new_pin_link = ManualParcelPINLink(
            workflow_id=1,
            zooniverse_subject_id=6,
            zoon_subject_id=6,
            zoon_workflow_id=1,
            parcel_pin='mppl-test-pin-1',
            comments="This should get linked to a Parcel"
        )
        new_pin_link.save()

        # Do I need to retrieve it again? Looks like it.
        parcel_lot_10 = Parcel.objects.get(workflow_id=1, pin_primary='mppl-test-pin-1')
        
        self.assertEqual(new_pin_link.zooniverse_subject.bool_parcel_match, True)
        self.assertIn(parcel_lot_10, new_pin_link.zooniverse_subject.parcel_matches.all())
        self.assertEqual(parcel_lot_10.bool_covenant, True)

    def test_parcel_match_manual_parcel_pin_1(self):
        parcel_lot_11 = Parcel.objects.get(workflow_id=1, pin_primary='mppl-test-pin-2')
        zoon_subject_6 = ZooniverseSubject.objects.get(workflow_id=1, pk=6)
      
        self.assertEqual(zoon_subject_6.bool_parcel_match, True)
        self.assertIn(parcel_lot_11, zoon_subject_6.parcel_matches.all())
        self.assertEqual(parcel_lot_11.bool_covenant, True)

    def test_parcel_match_manual_covenant_parcel_pin_1(self):
        ''' Create a new ManualCovenantParcelPINLink manually, re-check parcel match '''
        parcel_lot_10 = Parcel.objects.get(workflow_id=1, pin_primary='mppl-test-pin-1')

        new_pin_link = ManualCovenantParcelPINLink(
            workflow_id=1,
            manual_covenant_id=3,
            parcel_pin='mppl-test-pin-1',
            comments="This should get linked to a Parcel"
        )
        new_pin_link.save()

        # Do I need to retrieve it again? Looks like it.
        parcel_lot_10 = Parcel.objects.get(workflow_id=1, pin_primary='mppl-test-pin-1')
        
        self.assertEqual(new_pin_link.manual_covenant.bool_parcel_match, True)
        self.assertIn(parcel_lot_10, new_pin_link.manual_covenant.parcel_matches.all())
        self.assertEqual(parcel_lot_10.bool_covenant, True)

    def test_parcel_match_manual_covenant_parcel_pin_2(self):
        ''' Does match_parcels correctly perform on a ManualCovenantParcelPINLink that is already in the database? '''
        parcel_lot_11 = Parcel.objects.get(workflow_id=1, pin_primary='mppl-test-pin-2')
        man_cov_4 = ManualCovenant.objects.get(workflow_id=1, pk=4)
        
        self.assertEqual(man_cov_4.bool_parcel_match, True)
        self.assertIn(parcel_lot_11, man_cov_4.parcel_matches.all())
        self.assertEqual(parcel_lot_11.bool_covenant, True)