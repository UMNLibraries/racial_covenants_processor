import re
import os
from django.db import models
from django.utils.html import mark_safe
from postgres_copy import CopyManager
from django.apps import apps

from racial_covenants_processor.storage_backends import PrivateMediaStorage, PublicMediaStorage, PublicDeedStorage
from apps.zoon.models import ZooniverseWorkflow, ZooniverseSubject


class MatchTerm(models.Model):
    """A term found in a DeedPage during covenant detection in the initial processing stage. Could be a term indicating a racial covenant OR an exception, like an indicator of a birth certificate or military discharge."""
    term = models.CharField(max_length=100, db_index=True)

    def __str__(self):
        return self.term


class DeedPage(models.Model):
    """
    Each DeedPage object represents a single page of a property 
    record that has been uploaded, processed, and ingested into the
    Django portion of the Deed Machine. Multi-page documents like
    multi-page TIF files will be split into individual DeedPage objects during
    initial processing.
    """
    workflow = models.ForeignKey(
        ZooniverseWorkflow, on_delete=models.CASCADE, null=True)
    """Foreign key to associated workflow"""
    s3_lookup = models.CharField(blank=True, max_length=500, db_index=True)
    """Unique identifier of this page's image on S3"""
    doc_num = models.CharField(blank=True, null=True, max_length=101, db_index=True)
    """County document number. Not unique as some documents will have several or many pages. Some county documents don't have document numbers, but rather are identifed by Book and Page. In those cases, a doc_num is constructed by a book and page combination. Doc num can come from S3 metadata extracted via regex or be manually created and linked by using a supplemental information file at the time of Django import after initial processing."""
    doc_alt_id = models.CharField(blank=True, max_length=102, db_index=True)
    """An optional alternate document ID."""
    batch_id = models.CharField(blank=True, null=True, max_length=255)
    """An optional designator of batch, often referring to the parent folder an image was supplied in."""
    book_id = models.CharField(blank=True, null=True, max_length=103, db_index=True)
    """Book ID. Not present for all records or all counties."""
    page_num = models.IntegerField(null=True, db_index=True)
    """Page number of original record. Not present for all records or all counties. Note the difference with split_page_num, which is an automatically generated page number used to differentiate pages programmatically split in the Deed Machine process, usually with multi-page TIF file."""
    split_page_num = models.IntegerField(null=True, db_index=True)
    """Alternate page numbering that happens when a multipage image file (generally a TIF) has been split by the ingestion process. Note the difference to page_num, which is a page number value supplied with the original record in the county's numbering system."""
    doc_date = models.DateField(null=True, db_index=True)
    """Date of document."""
    doc_type = models.CharField(blank=True, null=True, max_length=104)
    """Document type, e.g. deed, Torrens certificate, mortgage, etc."""
    public_uuid = models.CharField(blank=True, max_length=50, db_index=True)
    """The randomly generated UUID created for the web version of this image in order to deter systematically scraping of publicly visible data. Generated by initial processing stage."""
    page_image_web = models.ImageField(
        storage=PublicDeedStorage(), max_length=200, null=True)
    """ImageField that stores a link to web-friendly, watermarked JPEG used for transcription"""
    page_stats = models.FileField(
        storage=PrivateMediaStorage(), max_length=200, null=True)
    """FileField that stores a link to metadata JSON file generated about the image during the OCR process, including how much is determined to be handwritten."""
    page_ocr_text = models.FileField(
        storage=PrivateMediaStorage(), max_length=200, null=True)
    """FileField that stores a link to a .txt file containing the concatenated full text of the page extracted by OCR."""
    page_ocr_json = models.FileField(
        storage=PrivateMediaStorage(), max_length=200, null=True)
    """FileField that stores a link to the complete Textract JSON OCR result for this page, including much more metadata and contextural information than page_ocr_text."""
    bool_match = models.BooleanField(default=False, db_index=True)
    """Is there a suspected covenant?"""
    bool_exception = models.BooleanField(default=False, db_index=True)
    """Was a disqualifying term found that exempts this from transcription? (E.G. a death certificate or military discharge)"""
    bool_manual = models.BooleanField(default=False, db_index=True)
    """ Has bool_match or bool_exception been manually overwritten? """
    matched_terms = models.ManyToManyField(MatchTerm)
    """M2M field storing which potential racial covenant (or exception) terms were matched, if any"""

    # These fields aid in setting up Zooniverse images
    doc_page_count = models.IntegerField(null=True)
    """How many pages does the Deed Machine think make up this document? Aids in Zooniverse setup."""
    prev_page_image_web = models.ImageField(
        storage=PublicDeedStorage(), max_length=201, null=True, db_index=True)
    """ImageField link to web-friendly image of previous page (by Deed Machine's calculation). Used to show previous page in Zooniverse if this is a potential covenant needing transcription."""
    next_page_image_web = models.ImageField(
        storage=PublicDeedStorage(), max_length=202, null=True, db_index=True)
    """ImageField link to web-friendly image of following page (by Deed Machine's calculation). Used to show following page in Zooniverse if this is a potential covenant needing transcription."""
    next_next_page_image_web = models.ImageField(
        storage=PublicDeedStorage(), max_length=203, null=True, db_index=True)
    """ImageField link to web-friendly image of following page of the following page (e.g. this page + 2) (by Deed Machine's calculation). Used to show following page of the following page in Zooniverse if this is a potential covenant needing transcription."""

    page_image_web_highlighted = models.ImageField(
        storage=PublicDeedStorage(), max_length=201, null=True, db_index=True)
    """ImageField that stores a link to web-friendly, watermarked, and highlighted JPEG used for transcription"""

    prev_page_image_lookup = models.CharField(
        blank=True, max_length=201, null=True)
    """Same idea as prev_page_image_web, except this is the s3_lookup of the previous page rather than a link to the image."""
    next_page_image_lookup = models.CharField(
        blank=True, max_length=202, null=True)
    """Same idea as next_page_image_web, except this is the s3_lookup of the previous page rather than a link to the image."""
    next_next_page_image_lookup = models.CharField(
        blank=True, max_length=203, null=True)
    """Same idea as next_next_page_image_web, except this is the s3_lookup of the previous page rather than a link to the image."""

    zooniverse_subject = models.ForeignKey(
        ZooniverseSubject, on_delete=models.SET_NULL, related_name='subject_legacy', null=True)
    """After post-Zooniverse ingestion of subjects, used to join to the matching subject for this if it's a hit"""

    # This is assuming that each page can only be in a given position for a single Zooniverse Subject, even though the same page could be part of each Zooniverse Subject's prev/next images
    zooniverse_subject_1st_page = models.ForeignKey(
        ZooniverseSubject, on_delete=models.SET_NULL, related_name='subject_1st_page', null=True)
    """After post-Zooniverse ingestion of subjects, used to join to the matching subject for this if it's a hit. Assists in giving access to DeedPage record for editors in the manual correction process. This is assuming that each page can only be in a given position for a single Zooniverse Subject, even though the same page could be part of each Zooniverse Subject's prev/next images"""
    zooniverse_subject_2nd_page = models.ForeignKey(
        ZooniverseSubject, on_delete=models.SET_NULL, related_name='subject_2nd_page', null=True)
    """After post-Zooniverse ingestion of subjects, used to join to the matching subject for this if it's a hit. Assists in giving access to DeedPage record for editors in the manual correction process. This is assuming that each page can only be in a given position for a single Zooniverse Subject, even though the same page could be part of each Zooniverse Subject's prev/next images"""
    zooniverse_subject_3rd_page = models.ForeignKey(
        ZooniverseSubject, on_delete=models.SET_NULL, related_name='subject_3rd_page', null=True)
    """After post-Zooniverse ingestion of subjects, used to join to the matching subject for this if it's a hit. Assists in giving access to DeedPage record for editors in the manual correction process. This is assuming that each page can only be in a given position for a single Zooniverse Subject, even though the same page could be part of each Zooniverse Subject's prev/next images"""
    objects = CopyManager()

    class Meta:
        indexes = [
            models.Index(fields=['-id'], name='id_desc'),
            models.Index(fields=['-id', 'workflow_id'], name='id_workflow_index'),
            models.Index(fields=['workflow_id', '-id'], name='workflow_id_index'),
            models.Index(fields=['workflow_id'], name='workflow_only_index')
        ]

    @property
    def thumbnail_preview(self):
        """Used to display thumbnail of DeedPage in admin view."""
        if self.page_image_web_highlighted:
            return mark_safe(f'<a href="{self.page_image_web_highlighted.url}" target="_blank"><img src="{self.page_image_web_highlighted.url}" width="100" /></a>')
        elif self.page_image_web:
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
            'doc_type': self.doc_type,
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
                doc_num_regex = re.compile(fr'(.+)((?<!\d){self.page_num}(?!\d))')
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
    """Foreign key to associated workflow"""
    report_csv = models.FileField(
        storage=PublicMediaStorage(), upload_to="analysis/", null=True)
    """FileField linking to CSV stored on s3 showing results of hit ingestion"""
    num_hits = models.IntegerField(null=True)
    """Number of DeedPage records with at least one hit"""
    num_exceptions = models.IntegerField(null=True)
    """Number of DeedPage records with at least one exception term, which will shield it from transcription."""
    created_at = models.DateTimeField()

    def __str__(self):
        return f"{self.workflow.workflow_name}, {self.created_at}"
