import pandas as pd

from django.test import TestCase

from apps.deed.models import DeedPage
from apps.zoon.models import ZooniverseWorkflow

from apps.deed.utils.deed_pagination import tag_prev_next_image_sql, tag_doc_num_page_counts


class DeedPagePaginationTests(TestCase):
    fixtures = ['deed', 'zoon']

    def test_tag_doc_num_page_counts(self):
        df = pd.DataFrame([
            {'doc_num': '1', 'public_uuid': 'aasdf'},
            {'doc_num': '1', 'public_uuid': 'basdf'},
            {'doc_num': '2', 'public_uuid': 'casdf'},
            {'doc_num': '2', 'public_uuid': 'dasdf'},
            {'doc_num': '2', 'public_uuid': 'easdf'},
            {'doc_num': '4', 'public_uuid': 'fasdf'},
            {'doc_num': '6', 'public_uuid': 'gasdf'},
            {'doc_num': '10', 'public_uuid': 'hasdf'},
            {'doc_num': '17', 'public_uuid': 'iasdf'},
        ])

        df = tag_doc_num_page_counts(df)
        # print(df[df['doc_num'] == '1']['doc_page_count'].iloc[0])

        self.assertEqual(df[df['doc_num'] == '1']['doc_page_count'].iloc[0], 2)
        self.assertEqual(df[df['doc_num'] == '2']['doc_page_count'].iloc[0], 3)
        self.assertEqual(df[df['doc_num'] == '17']['doc_page_count'].iloc[0], 1)


class DeedPagePrevNextTests(TestCase):
    fixtures = ['deed', 'zoon']

    # def setUp(self):
    #     # Set up database first time
    #     workflow = ZooniverseWorkflow.objects.get(pk=1)
    #     tag_prev_next_image_sql(workflow, True)
    #     # tag_prev_next_records(workflow, True)

    @classmethod
    def setUpTestData(cls):
        # Set up data for the whole TestCase
        workflow = ZooniverseWorkflow.objects.get(pk=1)
        tag_prev_next_image_sql(workflow, True)

    def test_prev_next_doc_num_page_2(self):

        deed_page = DeedPage.objects.get(
            s3_lookup='Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_1234_book_NONE_page_2'
        )
        # print(deed_page.prev_page_image_web)

        self.assertEqual(deed_page.prev_page_image_web.__str__(), 'web/fake/DEEDS/doc_1234_book_NONE_page_1.jpg')
        self.assertEqual(deed_page.next_page_image_web.__str__(), 'web/fake/DEEDS/doc_1234_book_NONE_page_3.jpg')
        self.assertEqual(deed_page.next_next_page_image_web.__str__(), 'web/fake/DEEDS/doc_1234_book_NONE_page_4.jpg')

    def test_prev_next_deed_page_doc_num_page_2(self):

        deed_page_1 = DeedPage.objects.get(
            s3_lookup='Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_1234_book_NONE_page_1'
        )

        deed_page_2 = DeedPage.objects.get(
            s3_lookup='Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_1234_book_NONE_page_2'
        )

        deed_page_3 = DeedPage.objects.get(
            s3_lookup='Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_1234_book_NONE_page_3'
        )

        deed_page_4 = DeedPage.objects.get(
            s3_lookup='Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_1234_book_NONE_page_4'
        )

        self.assertEqual(deed_page_1.prev_deedpage, None)
        self.assertEqual(deed_page_1.next_deedpage, deed_page_2)
        self.assertEqual(deed_page_1.next_next_deedpage, deed_page_3)

        self.assertEqual(deed_page_2.prev_deedpage, deed_page_1)
        self.assertEqual(deed_page_2.next_deedpage, deed_page_3)
        self.assertEqual(deed_page_2.next_next_deedpage, deed_page_4)

    def test_prev_next_deed_page_doc_num_has_page_num(self):

        deed_page = DeedPage.objects.get(
            s3_lookup='Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_NONE_book_107_page_548'
        )
        # print(deed_page.prev_deedpage)

        deed_page_547 = DeedPage.objects.get(
            s3_lookup='Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_NONE_book_107_page_547'
        )

        deed_page_549 = DeedPage.objects.get(
            s3_lookup='Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_NONE_book_107_page_549'
        )

        deed_page_550 = DeedPage.objects.get(
            s3_lookup='Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_NONE_book_107_page_550'
        )

        self.assertEqual(deed_page.prev_deedpage, deed_page_547)
        self.assertEqual(deed_page.next_deedpage, deed_page_549)
        self.assertEqual(deed_page.next_next_deedpage, deed_page_550)

    # x - doc num with no pages?
    def test_prev_next_doc_num_no_page(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            prev_page_image_web: None
            next_page_image_web: None
        """

        deed_page = DeedPage.objects.get(
            s3_lookup='9779605'
        )
        # print(deed_page.prev_page_image_web)

        self.assertEqual(deed_page.prev_page_image_web.__str__(), '')
        self.assertEqual(deed_page.next_page_image_web.__str__(), '')
        self.assertEqual(deed_page.next_next_page_image_web.__str__(), '')


    def test_prev_next_deed_page_doc_num_page_4(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            prev_page_image_web: doc_1234_book_NONE_page_3
            next_page_image_web: None
        """

        deed_page = DeedPage.objects.get(
            s3_lookup='Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_1234_book_NONE_page_4'
        )

        deed_page_3 = DeedPage.objects.get(
            s3_lookup='Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_1234_book_NONE_page_3'
        )

        self.assertEqual(deed_page.prev_deedpage, deed_page_3)
        self.assertEqual(deed_page.next_deedpage, None)
        self.assertEqual(deed_page.next_next_deedpage, None)

    # x - no doc_num, book and page only, no splitpage
    def test_prev_next_book_only_page_2(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            page count: 1
            prev_page_image_web: doc_NONE_book_140_page_1
            next_page_image_web: doc_NONE_book_140_page_3
        """

        deed_page = DeedPage.objects.get(
            s3_lookup='Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_NONE_book_140_page_2'
        )

        self.assertEqual(deed_page.prev_page_image_web.__str__(), 'web/fake/DEEDS/doc_NONE_book_140_page_1.jpg')
        self.assertEqual(deed_page.next_page_image_web.__str__(), 'web/fake/DEEDS/doc_NONE_book_140_page_3.jpg')
        self.assertEqual(deed_page.next_next_page_image_web.__str__(), 'web/fake/DEEDS/doc_NONE_book_140_page_4.jpg')

    def test_prev_next_book_only_page_4(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            page count: 1
            prev_page_image_web: doc_NONE_book_140_page_3
            next_page_image_web: None
        """

        deed_page = DeedPage.objects.get(
            s3_lookup='Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_NONE_book_140_page_4'
        )

        # self.assertEqual(doc_page_count, 1)
        self.assertEqual(deed_page.prev_page_image_web.__str__(), 'web/fake/DEEDS/doc_NONE_book_140_page_3.jpg')
        self.assertEqual(deed_page.next_page_image_web.__str__(), '')
        self.assertEqual(deed_page.next_next_page_image_web.__str__(), '')

    def test_prev_next_book_only_page_1(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            page count: 1
            prev_page_image_web: None
            next_page_image_web: doc_NONE_book_140_page_2
        """

        deed_page = DeedPage.objects.get(
            s3_lookup='Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_NONE_book_140_page_1'
        )

        # self.assertEqual(doc_page_count, 1)
        self.assertEqual(deed_page.prev_page_image_web.__str__(), '')
        self.assertEqual(deed_page.next_page_image_web.__str__(), 'web/fake/DEEDS/doc_NONE_book_140_page_2.jpg')
        self.assertEqual(deed_page.next_next_page_image_web.__str__(), 'web/fake/DEEDS/doc_NONE_book_140_page_3.jpg')

    # x - no doc_num, book and page only, splitpage
    def test_prev_next_book_only_page_2_splitpage(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            prev_page_image_web: doc_NONE_book_140_page_200_SPLITPAGE_1
            next_page_image_web: doc_NONE_book_140_page_200_SPLITPAGE_3
        """

        deed_page = DeedPage.objects.get(
            s3_lookup='Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_NONE_book_140_page_200_SPLITPAGE_2'
        )

        # # self.assertEqual(doc_page_count, 1)
        self.assertEqual(deed_page.prev_page_image_web.__str__(), 'web/fake/DEEDS/doc_NONE_book_140_page_200_SPLITPAGE_1.jpg')
        self.assertEqual(deed_page.next_page_image_web.__str__(), 'web/fake/DEEDS/doc_NONE_book_140_page_200_SPLITPAGE_3.jpg')
        self.assertEqual(deed_page.next_next_page_image_web.__str__(), 'web/fake/DEEDS/doc_NONE_book_140_page_200_SPLITPAGE_4.jpg')

    def test_prev_next_book_only_page_4_splitpage(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            prev_page_image_web: doc_NONE_book_140_page_200_SPLITPAGE_3
            next_page_image_web: None
        """

        deed_page = DeedPage.objects.get(
            s3_lookup='Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_NONE_book_140_page_200_SPLITPAGE_4'
        )

        self.assertEqual(deed_page.prev_page_image_web.__str__(), 'web/fake/DEEDS/doc_NONE_book_140_page_200_SPLITPAGE_3.jpg')
        self.assertEqual(deed_page.next_page_image_web.__str__(), '')
        self.assertEqual(deed_page.next_next_page_image_web.__str__(), '')

    def test_prev_next_book_only_page_1_splitpage(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            prev_page_image_web: None (This is a choice, another answer could be it should return the last available item from the previous page number, but that seems very complicated and hopefully an edge case that mostly impacts odd notes stapled to docs rather than previous pages on a multipage TIF)
            next_page_image_web: doc_NONE_book_140_page_200_SPLITPAGE_2.jpg
        """

        deed_page = DeedPage.objects.get(
            s3_lookup='Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_NONE_book_140_page_200_SPLITPAGE_1'
        )

        self.assertEqual(deed_page.prev_page_image_web.__str__(), '')
        self.assertEqual(deed_page.next_page_image_web.__str__(), 'web/fake/DEEDS/doc_NONE_book_140_page_200_SPLITPAGE_2.jpg')
        self.assertEqual(deed_page.next_next_page_image_web.__str__(), 'web/fake/DEEDS/doc_NONE_book_140_page_200_SPLITPAGE_3.jpg')

    # TODO: doc num with splitpages (see Dakota Torrens)
    def test_prev_next_doc_num_no_page_splitpage_1(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            prev_page_image_web: None
            next_page_image_web: doc_9991_book_NONE_page_NONE_SPLITPAGE_2.jpg
        """

        deed_page = DeedPage.objects.get(
            s3_lookup='Torrens_Images_Docs 1-24000 by Doc #/TORRENS_DOC_OTHER/doc_9991_book_NONE_page_NONE_SPLITPAGE_1'
        )

        self.assertEqual(deed_page.prev_page_image_web.__str__(), '')
        self.assertEqual(deed_page.next_page_image_web.__str__(), 'web/fake/TORRENS_DOC_OTHER/doc_9991_book_NONE_page_NONE_SPLITPAGE_2.jpg')
        self.assertEqual(deed_page.next_next_page_image_web.__str__(), 'web/fake/TORRENS_DOC_OTHER/doc_9991_book_NONE_page_NONE_SPLITPAGE_3.jpg')

    def test_prev_next_doc_num_no_page_splitpage_2(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            prev_page_image_web: doc_9991_book_NONE_page_NONE_SPLITPAGE_1.jpg
            next_page_image_web: doc_9991_book_NONE_page_NONE_SPLITPAGE_3.jpg
        """

        deed_page = DeedPage.objects.get(
            s3_lookup='Torrens_Images_Docs 1-24000 by Doc #/TORRENS_DOC_OTHER/doc_9991_book_NONE_page_NONE_SPLITPAGE_2'
        )

        self.assertEqual(deed_page.prev_page_image_web.__str__(), 'web/fake/TORRENS_DOC_OTHER/doc_9991_book_NONE_page_NONE_SPLITPAGE_1.jpg')
        self.assertEqual(deed_page.next_page_image_web.__str__(), 'web/fake/TORRENS_DOC_OTHER/doc_9991_book_NONE_page_NONE_SPLITPAGE_3.jpg')
        self.assertEqual(deed_page.next_next_page_image_web.__str__(), 'web/fake/TORRENS_DOC_OTHER/doc_9991_book_NONE_page_NONE_SPLITPAGE_4.jpg')

    def test_prev_next_doc_num_no_page_splitpage_4(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            prev_page_image_web: doc_9991_book_NONE_page_NONE_SPLITPAGE_3.jpg
            next_page_image_web: None
        """

        deed_page = DeedPage.objects.get(
            s3_lookup='Torrens_Images_Docs 1-24000 by Doc #/TORRENS_DOC_OTHER/doc_9991_book_NONE_page_NONE_SPLITPAGE_4'
        )

        self.assertEqual(deed_page.prev_page_image_web.__str__(), 'web/fake/TORRENS_DOC_OTHER/doc_9991_book_NONE_page_NONE_SPLITPAGE_3.jpg')
        self.assertEqual(deed_page.next_page_image_web.__str__(), '')
        self.assertEqual(deed_page.next_next_page_image_web.__str__(), '')

    # TODO: doc num with multiple pages + splitpage

    # Milwaukee examples
    def test_prev_next_milw_doc_num_page_2_only_2(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            prev_page_image_web: 02806155_NOTINDEX_0001.jpg
            next_page_image_web: None
            next_next_page_image_web: None
        """

        deed_page = DeedPage.objects.get(
            s3_lookup='30000102/02806155_NOTINDEX_0002'
        )

        self.assertEqual(deed_page.prev_page_image_web.__str__(), 'web/fake/30000102/02806155_NOTINDEX_0001.jpg')
        self.assertEqual(deed_page.next_page_image_web.__str__(), '')
        self.assertEqual(deed_page.next_next_page_image_web.__str__(), '')

    def test_prev_next_milw_doc_num_page_2_of_3(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            prev_page_image_web: 02806155_NOTINDEX_0001.jpg
            next_page_image_web: None
            next_next_page_image_web: None
        """

        deed_page = DeedPage.objects.get(
            s3_lookup='30000102/02720303_NOTINDEX_0002'
        )

        self.assertEqual(deed_page.prev_page_image_web.__str__(), 'web/fake/30000102/02720303_NOTINDEX_0001.jpg')
        self.assertEqual(deed_page.next_page_image_web.__str__(), 'web/fake/30000102/02720303_NOTINDEX_0003.jpg')
        self.assertEqual(deed_page.next_next_page_image_web.__str__(), '')

    def test_prev_next_milw_doc_num_page_1_of_3(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            prev_page_image_web: None
            next_page_image_web: 02806155_NOTINDEX_0002.jpg
            next_next_page_image_web: 02806155_NOTINDEX_0003.jpg
        """

        deed_page = DeedPage.objects.get(
            s3_lookup='30000102/02720303_NOTINDEX_0001'
        )

        self.assertEqual(deed_page.prev_page_image_web.__str__(), '')
        self.assertEqual(deed_page.next_page_image_web.__str__(), 'web/fake/30000102/02720303_NOTINDEX_0002.jpg')
        self.assertEqual(deed_page.next_next_page_image_web.__str__(), 'web/fake/30000102/02720303_NOTINDEX_0003.jpg')

    def test_prev_next_olmsted_doc_num_and_book_1_page(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            prev_page_image_web: None
            next_page_image_web: None
            next_next_page_image_web: None
        """

        deed_page = DeedPage.objects.get(
            s3_lookup='OlmstedCountyAbstracts/OldDeedBooks/D-102/HDEED102192'
        )

        self.assertEqual(deed_page.prev_page_image_web.__str__(), '')
        self.assertEqual(deed_page.next_page_image_web.__str__(), '')
        self.assertEqual(deed_page.next_next_page_image_web.__str__(), '')

    def test_prev_next_olmsted_doc_num_no_book_id_1_page(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            prev_page_image_web: None
            next_page_image_web: None
            next_next_page_image_web: None
        """

        deed_page = DeedPage.objects.get(
            s3_lookup='OlmstedCountyAbstracts/OldDeedBooks/D-102/HDEED102193'
        )

        self.assertEqual(deed_page.prev_page_image_web.__str__(), '')
        self.assertEqual(deed_page.next_page_image_web.__str__(), '')
        self.assertEqual(deed_page.next_next_page_image_web.__str__(), '')

    def test_prev_next_olmsted_split_page(self):
        """Does deedpage find correct prev/next images?
        """

        deed_page = DeedPage.objects.get(
            s3_lookup='OlmstedCountyAbstracts/OldMortgageBooks/M-327/H272733_SPLITPAGE_1'
        )

        self.assertEqual(deed_page.prev_page_image_web.__str__(), '')
        self.assertEqual(deed_page.next_page_image_web.__str__(), 'web/fake/OlmstedCountyAbstracts/OldMortgageBooks/M-327/H272733_SPLITPAGE_2.jpg')
        self.assertEqual(deed_page.next_next_page_image_web.__str__(), '')

    def test_prev_next_olmsted_split_page_2(self):
        """Does deedpage find correct prev/next images?
        """

        deed_page = DeedPage.objects.get(
            s3_lookup='OlmstedCountyAbstracts/OldMortgageBooks/M-327/H272733_SPLITPAGE_2'
        )

        self.assertEqual(deed_page.prev_page_image_web.__str__(), 'web/fake/OlmstedCountyAbstracts/OldMortgageBooks/M-327/H272733_SPLITPAGE_1.jpg')
        self.assertEqual(deed_page.next_page_image_web.__str__(), '')
        self.assertEqual(deed_page.next_next_page_image_web.__str__(), '')

    def test_prev_next_olmsted_split_page_3(self):
        """Does deedpage find correct prev/next images and deedpage records??
        """

        deed_page_1 = DeedPage.objects.get(
            s3_lookup='OlmstedCountyAbstracts/OldDeedBooks/D-088/H27165_SPLITPAGE_1'
        )

        deed_page_2 = DeedPage.objects.get(
            s3_lookup='OlmstedCountyAbstracts/OldDeedBooks/D-088/H27165_SPLITPAGE_2'
        )

        self.assertEqual(deed_page_1.prev_page_image_web.__str__(), '')
        self.assertEqual(deed_page_1.next_page_image_web.__str__(), 'web/fake/OlmstedCountyAbstracts/OldDeedBooks/D-088/H27165_SPLITPAGE_2.jpg')
        self.assertEqual(deed_page_1.next_next_page_image_web.__str__(), '')

        self.assertEqual(deed_page_2.prev_page_image_web.__str__(), 'web/fake/OlmstedCountyAbstracts/OldDeedBooks/D-088/H27165_SPLITPAGE_1.jpg')
        self.assertEqual(deed_page_2.next_page_image_web.__str__(), '')
        self.assertEqual(deed_page_2.next_next_page_image_web.__str__(), '')

        self.assertEqual(deed_page_1.prev_deedpage, None)
        self.assertEqual(deed_page_1.next_deedpage, deed_page_2)
        self.assertEqual(deed_page_1.next_next_deedpage, None)

        self.assertEqual(deed_page_2.prev_deedpage, deed_page_1)
        self.assertEqual(deed_page_2.next_deedpage, None)
        self.assertEqual(deed_page_2.next_next_deedpage, None)