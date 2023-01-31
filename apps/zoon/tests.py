from django.test import TestCase

from apps.zoon.models import ZooniverseWorkflow
from apps.zoon.utils.zooniverse_load import build_zooniverse_manifest


class ZooniverseUploadTests(TestCase):
    fixtures = ['deed', 'zoon']

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
