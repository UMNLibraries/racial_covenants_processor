from django.db import models
from postgres_copy import CopyManager


class ZooniverseResponseRaw(models.Model):
    classification_id = models.IntegerField()
    user_name = models.CharField(max_length=100, blank=True, db_index=True)
    user_id = models.IntegerField(null=True, db_index=True)
    # user_ip = models.CharField(max_length=10, blank=True)  # Removed from import in order to reduce personal info stored in database
    workflow_id = models.IntegerField(null=True)
    workflow_name = models.CharField(max_length=100, blank=True, db_index=True)
    workflow_version = models.FloatField()
    created_at = models.DateTimeField()
    gold_standard = models.BooleanField(null=True)
    expert = models.BooleanField(null=True)
    metadata = models.JSONField()
    annotations = models.JSONField()
    subject_data = models.JSONField()
    subject_ids = models.IntegerField(db_index=True)
    subject_data_flat = models.JSONField(null=True)
    objects = CopyManager()


class Workflow(models.Model):
    zoon_id = models.IntegerField(null=True, db_index=True)
    workflow_name = models.CharField(max_length=100, db_index=True)


class PotentialMatch(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE)
    zoon_subject_id = models.IntegerField(db_index=True)
    bool_covenant = models.BooleanField(null=True)


class ZooniverseUser(models.Model):
    zoon_id = models.IntegerField(null=True, db_index=True)
    zoon_name = models.CharField(max_length=100, blank=True, db_index=True)


class ZooniverseResponseFlat(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE)
    subject = models.ForeignKey(PotentialMatch, on_delete=models.CASCADE)
    user = models.ForeignKey(ZooniverseUser, null=True, on_delete=models.SET_NULL)
    classification_id = models.IntegerField()

    bool_covenant = models.BooleanField(null=True)
    bool_outlier = models.BooleanField(default=False)
    covenant_text = models.TextField(blank=True)
    addition = models.CharField(max_length=500, blank=True)
    lot = models.TextField(blank=True)
    block = models.CharField(max_length=500, blank=True)
    seller = models.CharField(max_length=100, blank=True)
    buyer = models.CharField(max_length=100, blank=True)
    deed_date = models.DateField(null=True)

    dt_created = models.DateTimeField()
    dt_retired = models.DateTimeField(null=True)

    raw_match = models.ForeignKey(ZooniverseResponseRaw, null=True, on_delete=models.CASCADE)
