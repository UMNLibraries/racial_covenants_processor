from django.db import models
from django.utils.html import mark_safe
from postgres_copy import CopyManager

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
    page_num = models.IntegerField(null=True)
    doc_date = models.DateField(null=True, db_index=True)
    doc_type = models.CharField(blank=True, max_length=100)
    public_uuid = models.CharField(blank=True, max_length=50, db_index=True)
    page_image_web = models.ImageField(
        storage=PublicDeedStorage(), null=True)
    page_stats = models.FileField(
        storage=PrivateMediaStorage(), null=True)
    page_ocr_text = models.FileField(
        storage=PrivateMediaStorage(), null=True)
    page_ocr_json = models.FileField(
        storage=PrivateMediaStorage(), null=True)
    bool_match = models.BooleanField(default=False, db_index=True)
    bool_exception = models.BooleanField(default=False, db_index=True)
    matched_terms = models.ManyToManyField(MatchTerm)

    zooniverse_subject = models.ForeignKey(
        ZooniverseSubject, on_delete=models.SET_NULL, null=True)

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

    # Need to save through private media storage in gather_deed_images.py
    # @property
    # def page_ocr_text_link(self):
    #     if self.page_image_web:
    #         return mark_safe(f'<a href="{self.page_image_web.url}" target="_blank"><img src="{self.page_image_web.url}" width="100" /></a>')
    #     return ""


class SearchHitReport(models.Model):
    workflow = models.ForeignKey(
        ZooniverseWorkflow, on_delete=models.CASCADE, null=True)
    report_csv = models.FileField(
        storage=PublicMediaStorage(), upload_to="analysis/", null=True)
    num_hits = models.IntegerField(null=True)
    created_at = models.DateTimeField()

    def __str__(self):
        return f"{self.workflow.workflow_name}, {self.created_at}"
