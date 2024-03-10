import re
from django.db import models
from django.utils.html import mark_safe
from postgres_copy import CopyManager
from django.apps import apps

from racial_covenants_processor.storage_backends import PrivateMediaStorage, PublicMediaStorage, PublicDeedStorage
from apps.zoon.models import ZooniverseWorkflow, ZooniverseSubject


class MatchTerm(models.Model):
    term = models.CharField(max_length=100, db_index=True)

    def __str__(self):
        return self.term


class DeedPage(models.Model):
    workflow = models.ForeignKey(
        ZooniverseWorkflow, on_delete=models.CASCADE, null=True)
    s3_lookup = models.CharField(blank=True, max_length=500, db_index=True)
    doc_num = models.CharField(blank=True, max_length=100, db_index=True)
    doc_alt_id = models.CharField(blank=True, max_length=100, db_index=True)
    batch_id = models.CharField(blank=True, max_length=255)
    book_id = models.CharField(blank=True, max_length=100, db_index=True)
    page_num = models.IntegerField(null=True, db_index=True)
    split_page_num = models.IntegerField(null=True, db_index=True)  # Alternate page numbering that happens when a multipage image file has been split by the ingestion process
    doc_date = models.DateField(null=True, db_index=True)
    doc_type = models.CharField(blank=True, max_length=100)
    public_uuid = models.CharField(blank=True, max_length=50, db_index=True)
    page_image_web = models.ImageField(
        storage=PublicDeedStorage(), max_length=200, null=True)
    page_stats = models.FileField(
        storage=PrivateMediaStorage(), max_length=200, null=True)
    page_ocr_text = models.FileField(
        storage=PrivateMediaStorage(), max_length=200, null=True)
    page_ocr_json = models.FileField(
        storage=PrivateMediaStorage(), max_length=200, null=True)
    bool_match = models.BooleanField(default=False, db_index=True)
    bool_exception = models.BooleanField(default=False, db_index=True)
    bool_manual = models.BooleanField(default=False, db_index=True) # has bool_match or bool_exception been manually overwritten?
    matched_terms = models.ManyToManyField(MatchTerm)

    # These fields aid in setting up Zooniverse images
    doc_page_count = models.IntegerField(null=True)
    prev_page_image_web = models.ImageField(
        storage=PublicDeedStorage(), max_length=200, null=True, db_index=True)
    next_page_image_web = models.ImageField(
        storage=PublicDeedStorage(), max_length=200, null=True, db_index=True)
    next_next_page_image_web = models.ImageField(
        storage=PublicDeedStorage(), max_length=200, null=True, db_index=True)

    prev_page_image_lookup = models.CharField(
        blank=True, max_length=100, null=True)
    next_page_image_lookup = models.CharField(
        blank=True, max_length=100, null=True)
    next_next_page_image_lookup = models.CharField(
        blank=True, max_length=100, null=True)

    # Used to join to the matching subject for this if it's a hit
    zooniverse_subject = models.ForeignKey(
        ZooniverseSubject, on_delete=models.SET_NULL, related_name='subject_legacy', null=True)

    # This is assuming that each page can only be in a given position for a single Zooniverse Subject, even though the same page could be part of each Zooniverse Subject's prev/next images
    zooniverse_subject_1st_page = models.ForeignKey(
        ZooniverseSubject, on_delete=models.SET_NULL, related_name='subject_1st_page', null=True)
    zooniverse_subject_2nd_page = models.ForeignKey(
        ZooniverseSubject, on_delete=models.SET_NULL, related_name='subject_2nd_page', null=True)
    zooniverse_subject_3rd_page = models.ForeignKey(
        ZooniverseSubject, on_delete=models.SET_NULL, related_name='subject_3rd_page', null=True)

    class Meta:
        indexes = [
            models.Index(fields=['-id'], name='id_desc'),
            models.Index(fields=['-id', 'workflow_id'], name='id_workflow_index'),
            models.Index(fields=['workflow_id', '-id'], name='workflow_id_index'),
            models.Index(fields=['workflow_id'], name='workflow_only_index')
        ]

    @property
    def thumbnail_preview(self):
        if self.page_image_web:
            return mark_safe(f'<a href="{self.page_image_web.url}" target="_blank"><img src="{self.page_image_web.url}" width="100" /></a>')
        return ""

    @property
    def record_link(self):
        page_num = f"Page {self.page_num}" if self.page_num else ''
        split_page_num = f"Splitpage {self.split_page_num}" if self.split_page_num else ''
        return mark_safe(f'<a href="/admin/deed/deedpage/{self.pk}/change/" target="_blank">{self.doc_num} {page_num} {split_page_num}</a>')

    @property
    def prev_thumbnail_preview(self):
        if self.prev_page_image_web:
            return mark_safe(f'<div style="display: inline-block;"><a href="{self.prev_page_image_web.url}" target="_blank"><img src="{self.prev_page_image_web.url}" width="100" /></a><br/><a href="/admin/deed/deedpage/{self.prev_deedpage.pk}/change/" target="_blank">DeedPage record</a></div>')
        return ""

    @property
    def next_thumbnail_preview(self):
        pages = []
        if self.next_page_image_web:
            pages.append(f'<div style="display: inline-block;"><a href="{self.next_page_image_web.url}" target="_blank" style="margin: 10px"><img src="{self.next_page_image_web.url}" width="100" /></a><br/><a href="/admin/deed/deedpage/{self.next_deedpage.pk}/change/" target="_blank">DeedPage record</a></div>')
        if self.next_next_page_image_web:
            pages.append(f'<div style="display: inline-block;"><a href="{self.next_next_page_image_web.url}" target="_blank" style="margin: 10px"><img src="{self.next_next_page_image_web.url}" width="100" /></a><br/><a href="/admin/deed/deedpage/{self.next_next_deedpage.pk}/change/" target="_blank">DeedPage record</a></div>')
        return mark_safe(''.join(pages))

    def deedpage_offset_finder(self, offset):
        kwargs = {
            'workflow': self.workflow,
            'batch_id': self.batch_id,
            'book_id': self.book_id,

        }
        if self.split_page_num and self.split_page_num >= 1:
                kwargs['split_page_num'] = self.split_page_num + offset
                kwargs['page_num'] = self.page_num
                kwargs['doc_num'] = self.doc_num
        else:
            if self.page_num and self.page_num > 0:
                kwargs['page_num'] = self.page_num + offset

                # If the doc number includes the page number, then add offset to doc_num before attempting match
                doc_num_regex = re.compile(f'(.+)((?<!\d){self.page_num}(?!\d))')
                doc_num_match = re.search(doc_num_regex, self.doc_num)
                if doc_num_match:
                    kwargs['doc_num'] = re.sub(doc_num_regex, fr'\g<1>{self.page_num + offset}', self.doc_num)
                else:
                    kwargs['doc_num'] = self.doc_num

        try:
            # Avoid circular import on DeedPage
            return apps.get_model('deed', 'DeedPage').objects.get(**kwargs)
        except:
            # raise
            return None
        return None

    @property
    def prev_deedpage(self):
        return self.deedpage_offset_finder(-1)

    @property
    def next_deedpage(self):
        return self.deedpage_offset_finder(1)

    @property
    def next_next_deedpage(self):
        return self.deedpage_offset_finder(2)


class SearchHitReport(models.Model):
    workflow = models.ForeignKey(
        ZooniverseWorkflow, on_delete=models.CASCADE, null=True)
    report_csv = models.FileField(
        storage=PublicMediaStorage(), upload_to="analysis/", null=True)
    num_hits = models.IntegerField(null=True)
    created_at = models.DateTimeField()

    def __str__(self):
        return f"{self.workflow.workflow_name}, {self.created_at}"
