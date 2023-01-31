from django.test import TestCase

from apps.deed.models import DeedPage
from apps.zoon.models import ZooniverseWorkflow

from apps.deed.utils.deed_pagination import get_doc_num_page_counts, sort_doc_nums_by_page_count, update_docs_with_page_counts


class DeedPagePaginationTests(TestCase):
    fixtures = ['deed', 'zoon']

    def get_doc_page_counts_single(self):
        workflow = ZooniverseWorkflow.objects.get(pk=1)
        page_counts = get_doc_num_page_counts(workflow)
        page_count_records = sort_doc_nums_by_page_count(page_counts)
        update_docs_with_page_counts(workflow, page_count_records)

        deed_page = DeedPage.objects.filter(doc_num='9779605').first()

        self.assertEqual(deed_page.doc_page_count, 1)

    def get_doc_page_counts_multi(self):
        workflow = ZooniverseWorkflow.objects.get(pk=1)
        page_counts = get_doc_num_page_counts(workflow)
        page_count_records = sort_doc_nums_by_page_count(page_counts)
        update_docs_with_page_counts(workflow, page_count_records)

        deed_page = DeedPage.objects.filter(doc_num='DEEDS_book_140_page_200').first()

        self.assertEqual(deed_page.doc_page_count, 4)


class DeedPagePrevNextTests(TestCase):
    fixtures = ['deed', 'zoon']

    # x - doc num with no pages?
    def test_prev_next_doc_num_no_page(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            prev_page_image_web: None
            next_page_image_web: None
        """

        deed_page = DeedPage.hit_objects.get(
            s3_lookup='9779605'
        )

        self.assertEqual(deed_page.prev_page_image_web, None)
        self.assertEqual(deed_page.next_page_image_web, None)
        self.assertEqual(deed_page.next_next_page_image_web, None)

    # x - doc num with multiple pages
    def test_prev_next_doc_num_page_2(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            prev_page_image_web: doc_1234_book_NONE_page_1
            next_page_image_web: doc_1234_book_NONE_page_3
        """

        deed_page = DeedPage.hit_objects.get(
            s3_lookup='Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_1234_book_NONE_page_2'
        )

        self.assertEqual(deed_page.prev_page_image_web, 'web/fake/DEEDS/doc_1234_book_NONE_page_1.jpg')
        self.assertEqual(deed_page.next_page_image_web, 'web/fake/DEEDS/doc_1234_book_NONE_page_3.jpg')
        self.assertEqual(deed_page.next_next_page_image_web, 'web/fake/DEEDS/doc_1234_book_NONE_page_4.jpg')

    def test_prev_next_doc_num_page_4(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            prev_page_image_web: doc_1234_book_NONE_page_3
            next_page_image_web: None
        """

        deed_page = DeedPage.hit_objects.get(
            s3_lookup='Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_1234_book_NONE_page_4'
        )

        self.assertEqual(deed_page.prev_page_image_web, 'web/fake/DEEDS/doc_1234_book_NONE_page_3.jpg')
        self.assertEqual(deed_page.next_page_image_web, None)
        self.assertEqual(deed_page.next_next_page_image_web, None)

    # x - no doc_num, book and page only, no splitpage
    def test_prev_next_book_only_page_2(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            page count: 1
            prev_page_image_web: doc_NONE_book_140_page_1
            next_page_image_web: doc_NONE_book_140_page_3
        """

        deed_page = DeedPage.hit_objects.get(
            s3_lookup='Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_NONE_book_140_page_2'
        )

        self.assertEqual(deed_page.page_count, 1)
        self.assertEqual(deed_page.prev_page_image_web, 'web/fake/DEEDS/doc_NONE_book_140_page_1.jpg')
        self.assertEqual(deed_page.next_page_image_web, 'web/fake/DEEDS/doc_NONE_book_140_page_3.jpg')
        self.assertEqual(deed_page.next_next_page_image_web, 'web/fake/DEEDS/doc_NONE_book_140_page_4.jpg')

    def test_prev_next_book_only_page_4(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            page count: 1
            prev_page_image_web: doc_NONE_book_140_page_3
            next_page_image_web: None
        """

        deed_page = DeedPage.hit_objects.get(
            s3_lookup='Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_NONE_book_140_page_4'
        )

        self.assertEqual(deed_page.page_count, 1)
        self.assertEqual(deed_page.prev_page_image_web, 'web/fake/DEEDS/doc_NONE_book_140_page_3.jpg')
        self.assertEqual(deed_page.next_page_image_web, None)
        self.assertEqual(deed_page.next_next_page_image_web, None)

    def test_prev_next_book_only_page_1(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            page count: 1
            prev_page_image_web: None
            next_page_image_web: doc_NONE_book_140_page_2
        """

        deed_page = DeedPage.hit_objects.get(
            s3_lookup='Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_NONE_book_140_page_1'
        )

        self.assertEqual(deed_page.page_count, 1)
        self.assertEqual(deed_page.prev_page_image_web, None)
        self.assertEqual(deed_page.next_page_image_web, 'web/fake/DEEDS/doc_NONE_book_140_page_2.jpg')
        self.assertEqual(deed_page.next_next_page_image_web, 'web/fake/DEEDS/doc_NONE_book_140_page_3.jpg')

    # x - no doc_num, book and page only, splitpage
    def test_prev_next_book_only_page_2_splitpage(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            prev_page_image_web: doc_NONE_book_140_page_200_SPLITPAGE_1
            next_page_image_web: doc_NONE_book_140_page_200_SPLITPAGE_3
        """

        deed_page = DeedPage.hit_objects.get(
            s3_lookup='Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_NONE_book_140_page_200_SPLITPAGE_2'
        )

        # self.assertEqual(deed_page.page_count, 1)
        self.assertEqual(deed_page.prev_page_image_web, 'web/fake/DEEDS/doc_NONE_book_140_page_200_SPLITPAGE_1.jpg')
        self.assertEqual(deed_page.next_page_image_web, 'web/fake/DEEDS/doc_NONE_book_140_page_200_SPLITPAGE_3.jpg')
        self.assertEqual(deed_page.next_next_page_image_web, 'web/fake/DEEDS/doc_NONE_book_140_page_200_SPLITPAGE_4.jpg')

    def test_prev_next_book_only_page_4_splitpage(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            prev_page_image_web: doc_NONE_book_140_page_200_SPLITPAGE_3
            next_page_image_web: None
        """

        deed_page = DeedPage.hit_objects.get(
            s3_lookup='Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_NONE_book_140_page_200_SPLITPAGE_4'
        )

        # self.assertEqual(deed_page.page_count, 1)
        self.assertEqual(deed_page.prev_page_image_web, 'web/fake/DEEDS/doc_NONE_book_140_page_200_SPLITPAGE_3.jpg')
        self.assertEqual(deed_page.next_page_image_web, None)
        self.assertEqual(deed_page.next_next_page_image_web, None)

    def test_prev_next_book_only_page_1_splitpage(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            prev_page_image_web: None (This is a choice, another answer could be it should return the last available item from the previous page number, but that seems very complicated and hopefully an edge case that mostly impacts odd notes stapled to docs rather than previous pages on a multipage TIF)
            next_page_image_web: doc_NONE_book_140_page_200_SPLITPAGE_2.jpg
        """

        deed_page = DeedPage.hit_objects.get(
            s3_lookup='Abstract_Images_Books_Deeds 104-277 by Book and Page/DEEDS/doc_NONE_book_140_page_200_SPLITPAGE_1'
        )

        # self.assertEqual(deed_page.page_count, 1)
        self.assertEqual(deed_page.prev_page_image_web, None)
        self.assertEqual(deed_page.next_page_image_web, 'web/fake/DEEDS/doc_NONE_book_140_page_200_SPLITPAGE_2.jpg')
        self.assertEqual(deed_page.next_next_page_image_web, 'web/fake/DEEDS/doc_NONE_book_140_page_200_SPLITPAGE_3.jpg')

    # TODO: doc num with splitpages (see Dakota Torrens)
    def test_prev_next_doc_num_no_page_splitpage_1(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            prev_page_image_web: None
            next_page_image_web: doc_9991_book_NONE_page_NONE_SPLITPAGE_2.jpg
        """

        deed_page = DeedPage.hit_objects.get(
            s3_lookup='Torrens_Images_Docs 1-24000 by Doc #/TORRENS_DOC_OTHER/doc_9991_book_NONE_page_NONE_SPLITPAGE_1'
        )

        self.assertEqual(deed_page.prev_page_image_web, None)
        self.assertEqual(deed_page.next_page_image_web, 'web/fake/TORRENS_DOC_OTHER/doc_9991_book_NONE_page_NONE_SPLITPAGE_2.jpg')
        self.assertEqual(deed_page.next_next_page_image_web, 'web/fake/TORRENS_DOC_OTHER/doc_9991_book_NONE_page_NONE_SPLITPAGE_3.jpg')

    def test_prev_next_doc_num_no_page_splitpage_2(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            prev_page_image_web: doc_9991_book_NONE_page_NONE_SPLITPAGE_1.jpg
            next_page_image_web: doc_9991_book_NONE_page_NONE_SPLITPAGE_3.jpg
        """

        deed_page = DeedPage.hit_objects.get(
            s3_lookup='Torrens_Images_Docs 1-24000 by Doc #/TORRENS_DOC_OTHER/doc_9991_book_NONE_page_NONE_SPLITPAGE_2'
        )

        self.assertEqual(deed_page.prev_page_image_web, 'web/fake/TORRENS_DOC_OTHER/doc_9991_book_NONE_page_NONE_SPLITPAGE_1.jpg')
        self.assertEqual(deed_page.next_page_image_web, 'web/fake/TORRENS_DOC_OTHER/doc_9991_book_NONE_page_NONE_SPLITPAGE_3.jpg')
        self.assertEqual(deed_page.next_next_page_image_web, 'web/fake/TORRENS_DOC_OTHER/doc_9991_book_NONE_page_NONE_SPLITPAGE_4.jpg')

    def test_prev_next_doc_num_no_page_splitpage_4(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            prev_page_image_web: doc_9991_book_NONE_page_NONE_SPLITPAGE_3.jpg
            next_page_image_web: None
        """

        deed_page = DeedPage.hit_objects.get(
            s3_lookup='Torrens_Images_Docs 1-24000 by Doc #/TORRENS_DOC_OTHER/doc_9991_book_NONE_page_NONE_SPLITPAGE_4'
        )

        self.assertEqual(deed_page.prev_page_image_web, 'web/fake/TORRENS_DOC_OTHER/doc_9991_book_NONE_page_NONE_SPLITPAGE_3.jpg')
        self.assertEqual(deed_page.next_page_image_web, None)
        self.assertEqual(deed_page.next_next_page_image_web, None)

    # TODO: doc num with multiple pages + splitpage

    # Milwaukee examples
    def test_prev_next_milw_doc_num_page_2_only_2(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            prev_page_image_web: 02806155_NOTINDEX_0001.jpg
            next_page_image_web: None
            next_next_page_image_web: None
        """

        deed_page = DeedPage.hit_objects.get(
            s3_lookup='30000102/02806155_NOTINDEX_0002'
        )

        self.assertEqual(deed_page.prev_page_image_web, 'web/fake/30000102/02806155_NOTINDEX_0001.jpg')
        self.assertEqual(deed_page.next_page_image_web, None)
        self.assertEqual(deed_page.next_next_page_image_web, None)

    def test_prev_next_milw_doc_num_page_2_of_3(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            prev_page_image_web: 02806155_NOTINDEX_0001.jpg
            next_page_image_web: None
            next_next_page_image_web: None
        """

        deed_page = DeedPage.hit_objects.get(
            s3_lookup='30000102/02720303_NOTINDEX_0002'
        )

        self.assertEqual(deed_page.prev_page_image_web, 'web/fake/30000102/02720303_NOTINDEX_0001.jpg')
        self.assertEqual(deed_page.next_page_image_web, 'web/fake/30000102/02720303_NOTINDEX_0003.jpg')
        self.assertEqual(deed_page.next_next_page_image_web, None)

    def test_prev_next_milw_doc_num_page_1_of_3(self):
        """Does deedpage find correct prev/next images?
        In this case, should be:
            prev_page_image_web: None
            next_page_image_web: 02806155_NOTINDEX_0002.jpg
            next_next_page_image_web: 02806155_NOTINDEX_0003.jpg
        """

        deed_page = DeedPage.hit_objects.get(
            s3_lookup='30000102/02720303_NOTINDEX_0001'
        )

        self.assertEqual(deed_page.prev_page_image_web, None)
        self.assertEqual(deed_page.next_page_image_web, 'web/fake/30000102/02720303_NOTINDEX_0002.jpg')
        self.assertEqual(deed_page.next_next_page_image_web, 'web/fake/30000102/02720303_NOTINDEX_0003.jpg')
