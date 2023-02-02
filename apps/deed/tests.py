import pandas as pd

from django.test import TestCase

from apps.deed.models import DeedPage
from apps.zoon.models import ZooniverseWorkflow

from apps.deed.utils.deed_pagination import find_prev_next_image, tag_doc_num_page_counts


# class DeedPagePaginationTests(TestCase):
#     fixtures = ['deed', 'zoon']
#
#     def test_tag_doc_num_page_counts(self):
#         df = pd.DataFrame([
#             {'doc_num': '1', 'public_uuid': 'aasdf'},
#             {'doc_num': '1', 'public_uuid': 'basdf'},
#             {'doc_num': '2', 'public_uuid': 'casdf'},
#             {'doc_num': '2', 'public_uuid': 'dasdf'},
#             {'doc_num': '2', 'public_uuid': 'easdf'},
#             {'doc_num': '4', 'public_uuid': 'fasdf'},
#             {'doc_num': '6', 'public_uuid': 'gasdf'},
#             {'doc_num': '10', 'public_uuid': 'hasdf'},
#             {'doc_num': '17', 'public_uuid': 'iasdf'},
#         ])
#
#         df = tag_doc_num_page_counts(df)
#         print(df[df['doc_num'] == '1']['doc_page_count'].iloc[0])
#
#         self.assertEqual(df[df['doc_num'] == '1']['doc_page_count'].iloc[0], 2)
#         self.assertEqual(df[df['doc_num'] == '2']['doc_page_count'].iloc[0], 3)
#         self.assertEqual(df[df['doc_num'] == '17']['doc_page_count'].iloc[0], 1)
#
#
class DeedPagePrevNextTests(TestCase):
    fixtures = ['deed', 'zoon']

    def prev_next_shorthand(self, s3_lookup):

        doc_list = DeedPage.objects.all().values(
            'pk',
            'doc_num',
            'book_id',
            'doc_page_count',
            'page_num',
            'split_page_num',
            'page_image_web',
            's3_lookup'
        )

        td = [doc for doc in doc_list if doc['s3_lookup'] == s3_lookup][0]

        prev_image = find_prev_next_image(doc_list, td['doc_num'], td['book_id'], td['doc_page_count'], td['page_num'], td['split_page_num'], -1)
        next_image = find_prev_next_image(doc_list, td['doc_num'], td['book_id'], td['doc_page_count'], td['page_num'], td['split_page_num'], 1)
        next_next_image = find_prev_next_image(doc_list, td['doc_num'], td['book_id'], td['doc_page_count'], td['page_num'], td['split_page_num'], 2)

        return (prev_image, next_image, next_next_image,)

    # x - doc num with multiple pages
    def test_prev_next_doc_num_page_2(self):

        prev_image, next_image, next_next_image = self.prev_next_shorthand('Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_1234_book_NONE_page_2')

        self.assertEqual(prev_image, 'web/fake/DEEDS/doc_1234_book_NONE_page_1.jpg')
        self.assertEqual(next_image, 'web/fake/DEEDS/doc_1234_book_NONE_page_3.jpg')
        self.assertEqual(next_next_image, 'web/fake/DEEDS/doc_1234_book_NONE_page_4.jpg')

    # x - doc num with no pages?
    def test_prev_next_doc_num_no_page(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            prev_page_image_web: None
            next_page_image_web: None
        """

        prev_image, next_image, next_next_image = self.prev_next_shorthand('9779605')

        self.assertEqual(prev_image, None)
        self.assertEqual(next_image, None)
        self.assertEqual(next_next_image, None)

    def test_prev_next_doc_num_page_4(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            prev_page_image_web: doc_1234_book_NONE_page_3
            next_page_image_web: None
        """

        prev_image, next_image, next_next_image = self.prev_next_shorthand('Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_1234_book_NONE_page_4')

        self.assertEqual(prev_image, 'web/fake/DEEDS/doc_1234_book_NONE_page_3.jpg')
        self.assertEqual(next_image, None)
        self.assertEqual(next_next_image, None)

    # x - no doc_num, book and page only, no splitpage
    def test_prev_next_book_only_page_2(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            page count: 1
            prev_page_image_web: doc_NONE_book_140_page_1
            next_page_image_web: doc_NONE_book_140_page_3
        """

        prev_image, next_image, next_next_image = self.prev_next_shorthand('Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_NONE_book_140_page_2')

        # deed_page = DeedPage.hit_objects.get(
        #     s3_lookup='Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_NONE_book_140_page_2'
        # )

        # # self.assertEqual(doc_page_count, 1)
        self.assertEqual(prev_image, 'web/fake/DEEDS/doc_NONE_book_140_page_1.jpg')
        self.assertEqual(next_image, 'web/fake/DEEDS/doc_NONE_book_140_page_3.jpg')
        self.assertEqual(next_next_image, 'web/fake/DEEDS/doc_NONE_book_140_page_4.jpg')

    def test_prev_next_book_only_page_4(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            page count: 1
            prev_page_image_web: doc_NONE_book_140_page_3
            next_page_image_web: None
        """

        prev_image, next_image, next_next_image = self.prev_next_shorthand('Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_NONE_book_140_page_4')

        # deed_page = DeedPage.hit_objects.get(
        #     s3_lookup='Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_NONE_book_140_page_4'
        # )

        # self.assertEqual(doc_page_count, 1)
        self.assertEqual(prev_image, 'web/fake/DEEDS/doc_NONE_book_140_page_3.jpg')
        self.assertEqual(next_image, None)
        self.assertEqual(next_next_image, None)

    def test_prev_next_book_only_page_1(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            page count: 1
            prev_page_image_web: None
            next_page_image_web: doc_NONE_book_140_page_2
        """

        prev_image, next_image, next_next_image = self.prev_next_shorthand('Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_NONE_book_140_page_1')

        # deed_page = DeedPage.hit_objects.get(
        #     s3_lookup='Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_NONE_book_140_page_1'
        # )

        # self.assertEqual(doc_page_count, 1)
        self.assertEqual(prev_image, None)
        self.assertEqual(next_image, 'web/fake/DEEDS/doc_NONE_book_140_page_2.jpg')
        self.assertEqual(next_next_image, 'web/fake/DEEDS/doc_NONE_book_140_page_3.jpg')

    # x - no doc_num, book and page only, splitpage
    def test_prev_next_book_only_page_2_splitpage(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            prev_page_image_web: doc_NONE_book_140_page_200_SPLITPAGE_1
            next_page_image_web: doc_NONE_book_140_page_200_SPLITPAGE_3
        """

        prev_image, next_image, next_next_image = self.prev_next_shorthand('Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_NONE_book_140_page_200_SPLITPAGE_2')

        # deed_page = DeedPage.hit_objects.get(
        #     s3_lookup='Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_NONE_book_140_page_200_SPLITPAGE_2'
        # )

        # # self.assertEqual(doc_page_count, 1)
        self.assertEqual(prev_image, 'web/fake/DEEDS/doc_NONE_book_140_page_200_SPLITPAGE_1.jpg')
        self.assertEqual(next_image, 'web/fake/DEEDS/doc_NONE_book_140_page_200_SPLITPAGE_3.jpg')
        self.assertEqual(next_next_image, 'web/fake/DEEDS/doc_NONE_book_140_page_200_SPLITPAGE_4.jpg')

    def test_prev_next_book_only_page_4_splitpage(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            prev_page_image_web: doc_NONE_book_140_page_200_SPLITPAGE_3
            next_page_image_web: None
        """

        prev_image, next_image, next_next_image = self.prev_next_shorthand('Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_NONE_book_140_page_200_SPLITPAGE_4')

        # deed_page = DeedPage.hit_objects.get(
        #     s3_lookup='Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_NONE_book_140_page_200_SPLITPAGE_4'
        # )

        # # self.assertEqual(doc_page_count, 1)
        self.assertEqual(prev_image, 'web/fake/DEEDS/doc_NONE_book_140_page_200_SPLITPAGE_3.jpg')
        self.assertEqual(next_image, None)
        self.assertEqual(next_next_image, None)

    def test_prev_next_book_only_page_1_splitpage(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            prev_page_image_web: None (This is a choice, another answer could be it should return the last available item from the previous page number, but that seems very complicated and hopefully an edge case that mostly impacts odd notes stapled to docs rather than previous pages on a multipage TIF)
            next_page_image_web: doc_NONE_book_140_page_200_SPLITPAGE_2.jpg
        """

        prev_image, next_image, next_next_image = self.prev_next_shorthand('Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_NONE_book_140_page_200_SPLITPAGE_1')

        # deed_page = DeedPage.hit_objects.get(
        #     s3_lookup='Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_NONE_book_140_page_200_SPLITPAGE_1'
        # )

        # # self.assertEqual(doc_page_count, 1)
        self.assertEqual(prev_image, None)
        self.assertEqual(next_image, 'web/fake/DEEDS/doc_NONE_book_140_page_200_SPLITPAGE_2.jpg')
        self.assertEqual(next_next_image, 'web/fake/DEEDS/doc_NONE_book_140_page_200_SPLITPAGE_3.jpg')

    # TODO: doc num with splitpages (see Dakota Torrens)
    def test_prev_next_doc_num_no_page_splitpage_1(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            prev_page_image_web: None
            next_page_image_web: doc_9991_book_NONE_page_NONE_SPLITPAGE_2.jpg
        """

        prev_image, next_image, next_next_image = self.prev_next_shorthand('Torrens_Images_Docs 1-24000 by Doc #/TORRENS_DOC_OTHER/doc_9991_book_NONE_page_NONE_SPLITPAGE_1')

        # deed_page = DeedPage.hit_objects.get(
        #     s3_lookup='Torrens_Images_Docs 1-24000 by Doc #/TORRENS_DOC_OTHER/doc_9991_book_NONE_page_NONE_SPLITPAGE_1'
        # )

        self.assertEqual(prev_image, None)
        self.assertEqual(next_image, 'web/fake/TORRENS_DOC_OTHER/doc_9991_book_NONE_page_NONE_SPLITPAGE_2.jpg')
        self.assertEqual(next_next_image, 'web/fake/TORRENS_DOC_OTHER/doc_9991_book_NONE_page_NONE_SPLITPAGE_3.jpg')

    def test_prev_next_doc_num_no_page_splitpage_2(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            prev_page_image_web: doc_9991_book_NONE_page_NONE_SPLITPAGE_1.jpg
            next_page_image_web: doc_9991_book_NONE_page_NONE_SPLITPAGE_3.jpg
        """

        prev_image, next_image, next_next_image = self.prev_next_shorthand('Torrens_Images_Docs 1-24000 by Doc #/TORRENS_DOC_OTHER/doc_9991_book_NONE_page_NONE_SPLITPAGE_2')

        # deed_page = DeedPage.hit_objects.get(
        #     s3_lookup='Torrens_Images_Docs 1-24000 by Doc #/TORRENS_DOC_OTHER/doc_9991_book_NONE_page_NONE_SPLITPAGE_2'
        # )

        self.assertEqual(prev_image, 'web/fake/TORRENS_DOC_OTHER/doc_9991_book_NONE_page_NONE_SPLITPAGE_1.jpg')
        self.assertEqual(next_image, 'web/fake/TORRENS_DOC_OTHER/doc_9991_book_NONE_page_NONE_SPLITPAGE_3.jpg')
        self.assertEqual(next_next_image, 'web/fake/TORRENS_DOC_OTHER/doc_9991_book_NONE_page_NONE_SPLITPAGE_4.jpg')

    def test_prev_next_doc_num_no_page_splitpage_4(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            prev_page_image_web: doc_9991_book_NONE_page_NONE_SPLITPAGE_3.jpg
            next_page_image_web: None
        """

        prev_image, next_image, next_next_image = self.prev_next_shorthand('Torrens_Images_Docs 1-24000 by Doc #/TORRENS_DOC_OTHER/doc_9991_book_NONE_page_NONE_SPLITPAGE_4')

        # deed_page = DeedPage.hit_objects.get(
        #     s3_lookup='Torrens_Images_Docs 1-24000 by Doc #/TORRENS_DOC_OTHER/doc_9991_book_NONE_page_NONE_SPLITPAGE_4'
        # )

        self.assertEqual(prev_image, 'web/fake/TORRENS_DOC_OTHER/doc_9991_book_NONE_page_NONE_SPLITPAGE_3.jpg')
        self.assertEqual(next_image, None)
        self.assertEqual(next_next_image, None)

    # TODO: doc num with multiple pages + splitpage

    # Milwaukee examples
    def test_prev_next_milw_doc_num_page_2_only_2(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            prev_page_image_web: 02806155_NOTINDEX_0001.jpg
            next_page_image_web: None
            next_next_page_image_web: None
        """

        prev_image, next_image, next_next_image = self.prev_next_shorthand('30000102/02806155_NOTINDEX_0002')

        # deed_page = DeedPage.hit_objects.get(
        #     s3_lookup='30000102/02806155_NOTINDEX_0002'
        # )

        self.assertEqual(prev_image, 'web/fake/30000102/02806155_NOTINDEX_0001.jpg')
        self.assertEqual(next_image, None)
        self.assertEqual(next_next_image, None)

    def test_prev_next_milw_doc_num_page_2_of_3(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            prev_page_image_web: 02806155_NOTINDEX_0001.jpg
            next_page_image_web: None
            next_next_page_image_web: None
        """

        prev_image, next_image, next_next_image = self.prev_next_shorthand('30000102/02720303_NOTINDEX_0002')

        # deed_page = DeedPage.hit_objects.get(
        #     s3_lookup='30000102/02720303_NOTINDEX_0002'
        # )

        self.assertEqual(prev_image, 'web/fake/30000102/02720303_NOTINDEX_0001.jpg')
        self.assertEqual(next_image, 'web/fake/30000102/02720303_NOTINDEX_0003.jpg')
        self.assertEqual(next_next_image, None)

    def test_prev_next_milw_doc_num_page_1_of_3(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            prev_page_image_web: None
            next_page_image_web: 02806155_NOTINDEX_0002.jpg
            next_next_page_image_web: 02806155_NOTINDEX_0003.jpg
        """

        prev_image, next_image, next_next_image = self.prev_next_shorthand('30000102/02720303_NOTINDEX_0001')

        # deed_page = DeedPage.hit_objects.get(
        #     s3_lookup='30000102/02720303_NOTINDEX_0001'
        # )

        self.assertEqual(prev_image, None)
        self.assertEqual(next_image, 'web/fake/30000102/02720303_NOTINDEX_0002.jpg')
        self.assertEqual(next_next_image, 'web/fake/30000102/02720303_NOTINDEX_0003.jpg')
