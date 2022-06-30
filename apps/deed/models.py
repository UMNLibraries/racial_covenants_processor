from django.db import models
from django.utils.html import mark_safe
from postgres_copy import CopyManager

from racial_covenants_processor.storage_backends import PrivateMediaStorage
from apps.zoon.models import ZooniverseWorkflow, ZooniverseSubject


class DeedPage(models.Model):
    workflow = models.ForeignKey(
        ZooniverseWorkflow, on_delete=models.CASCADE, null=True)
    doc_num = models.CharField(blank=True, max_length=100)
    page_num = models.IntegerField(null=True)
    doc_date = models.DateField(null=True)
    doc_type = models.CharField(blank=True, max_length=100)
    page_image_web = models.ImageField(
        storage=PrivateMediaStorage(), null=True)
    page_ocr_text = models.FileField(
        storage=PrivateMediaStorage(), null=True)
    bool_match = models.BooleanField(default=False)
    matched_terms = models.JSONField(null=True)

    zooniverse_subject = models.ForeignKey(
        ZooniverseSubject, on_delete=models.SET_NULL, null=True)

    @property
    def thumbnail_preview(self):
        if self.page_image_web:
            return mark_safe(f'<a href="{self.page_image_web.url}" target="_blank"><img src="{self.page_image_web.url}" width="100" /></a>')
        return ""


class SearchHitReport(models.Model):
    workflow = models.ForeignKey(
        ZooniverseWorkflow, on_delete=models.CASCADE, null=True)
    report_csv = models.FileField(
        storage=PrivateMediaStorage(), null=True)
    num_hits = models.IntegerField(null=True)


'''NOTE: BELOW HERE THIS IS MOSTLY LEGACY CODE. ACTIVE WORK IS ALL IN THE "ZOON" APP'''


# class ZooniverseResponseRaw(models.Model):
#     classification_id = models.IntegerField()
#     user_name = models.CharField(max_length=100, blank=True, db_index=True)
#     user_id = models.IntegerField(null=True, db_index=True)
#     # user_ip = models.CharField(max_length=10, blank=True)  # Removed from import in order to reduce personal info stored in database
#     workflow_id = models.IntegerField(null=True)
#     workflow_name = models.CharField(max_length=100, blank=True, db_index=True)
#     workflow_version = models.FloatField()
#     created_at = models.DateTimeField()
#     gold_standard = models.BooleanField(null=True)
#     expert = models.BooleanField(null=True)
#     metadata = models.JSONField()
#     annotations = models.JSONField()
#     subject_data = models.JSONField()
#     subject_ids = models.IntegerField(db_index=True)
#     subject_data_flat = models.JSONField(null=True)
#     objects = CopyManager()
#
#
# class Workflow(models.Model):
#     zoon_id = models.IntegerField(null=True, db_index=True)
#     workflow_name = models.CharField(max_length=100, db_index=True)
#
#
# BOOL_COVENANT_CHOICES = (
#     ('Yes', 'No'),
#     ('No', 'No'),
#     ('Unclear', 'Unclear'),
#     ('Unprocessed', 'Unprocessed'),
# )
#
#
# class PotentialMatch(models.Model):
#     '''Future: Assign an id to correspond to a deed image pre-Zooniverse'''
#     workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE)
#     zoon_subject_id = models.IntegerField(db_index=True)
#     bool_covenant = models.BooleanField(null=True)
#
#
# class ZooniverseUser(models.Model):
#     zoon_id = models.IntegerField(null=True, db_index=True)
#     zoon_name = models.CharField(max_length=100, blank=True, db_index=True)
#
#
# class ZooniverseResponseFlat(models.Model):
#     workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE)
#     subject = models.ForeignKey(PotentialMatch, on_delete=models.CASCADE)
#     user = models.ForeignKey(ZooniverseUser, null=True,
#                              on_delete=models.SET_NULL)
#     classification_id = models.IntegerField()
#
#     bool_covenant = models.BooleanField(null=True)
#     bool_outlier = models.BooleanField(default=False)
#     covenant_text = models.TextField(blank=True)
#     addition = models.CharField(max_length=500, blank=True)
#     lot = models.TextField(blank=True)
#     block = models.CharField(max_length=500, blank=True)
#     seller = models.CharField(max_length=100, blank=True)
#     buyer = models.CharField(max_length=100, blank=True)
#     deed_date = models.DateField(null=True)
#
#     dt_created = models.DateTimeField()
#     dt_retired = models.DateTimeField(null=True)
#
#     raw_match = models.ForeignKey(
#         ZooniverseResponseRaw, null=True, on_delete=models.CASCADE)
#
#
# class ZooniverseUserRating(models.Model):
#     workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE)
#     user = models.ForeignKey(ZooniverseUser, on_delete=models.CASCADE)
#     cohen_kappa = models.FloatField(null=True)
#     n_clfs = models.IntegerField(null=True)
#     reliability_score = models.FloatField(null=True)
#     rank = models.IntegerField(null=True)
