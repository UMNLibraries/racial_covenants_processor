from django.db import models
from postgres_copy import CopyManager


class ZooniverseWorkflow(models.Model):
    zoon_id = models.IntegerField(null=True, db_index=True)
    workflow_name = models.CharField(max_length=100, db_index=True)

    def __str__(self):
        return self.workflow_name


class ZooniverseSubject(models.Model):
    '''Future: Assign an id to correspond to a deed image pre-Zooniverse'''
    workflow = models.ForeignKey(ZooniverseWorkflow, on_delete=models.CASCADE)
    zoon_subject_id = models.IntegerField(db_index=True)
    image_id = models.CharField(max_length=100, db_index=True)
    dt_retired = models.DateTimeField(null=True)

    # This part comes from the reducers
    bool_covenant = models.BooleanField(null=True)
    bool_problem = models.BooleanField(default=False)
    covenant_text = models.TextField(blank=True)
    addition = models.CharField(max_length=500, blank=True)
    lot = models.TextField(blank=True)
    block = models.CharField(max_length=500, blank=True)
    seller = models.CharField(max_length=100, blank=True)
    buyer = models.CharField(max_length=100, blank=True)
    deed_date = models.DateField(null=True)

    # Scores, also from the reducers
    bool_covenant_score = models.FloatField(null=True)
    covenant_text_score = models.FloatField(null=True)
    addition_score = models.FloatField(null=True)
    lot_score = models.FloatField(null=True)
    block_score = models.FloatField(null=True)
    seller_score = models.FloatField(null=True)
    buyer_score = models.FloatField(null=True)

    deed_date_overall_score = models.FloatField(null=True)
    deed_date_year_score = models.FloatField(null=True)
    deed_date_month_score = models.FloatField(null=True)
    deed_date_day_score = models.FloatField(null=True)

    def __str__(self):
        return f"{self.workflow} {self.zoon_subject_id}"


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

    # Joined after subjects loaded
    subject = models.ForeignKey(
        ZooniverseSubject, null=True, on_delete=models.SET_NULL)

    objects = CopyManager()


class ZooniverseResponseProcessed(models.Model):
    workflow = models.ForeignKey(ZooniverseWorkflow, on_delete=models.CASCADE)
    classification_id = models.IntegerField()
    user_name = models.CharField(max_length=100, blank=True, db_index=True)
    user_id = models.IntegerField(null=True, db_index=True)
    subject = models.ForeignKey(
        ZooniverseSubject, null=True, on_delete=models.SET_NULL)
    bool_covenant = models.CharField(max_length=100, null=True, blank=True)
    covenant_text = models.TextField(blank=True)
    addition = models.CharField(max_length=500, blank=True)
    lot = models.TextField(blank=True)
    block = models.CharField(max_length=500, blank=True)
    seller = models.CharField(max_length=100, blank=True)
    buyer = models.CharField(max_length=100, blank=True)
    deed_date_year = models.CharField(max_length=10, blank=True)
    deed_date_month = models.CharField(max_length=100, blank=True)
    deed_date_day = models.CharField(max_length=10, blank=True)
    created_at = models.DateTimeField()
    response_raw = models.ForeignKey(
        ZooniverseResponseRaw, on_delete=models.CASCADE, null=True)


class ZooniverseUser(models.Model):
    '''Temp: duplicated from deeds.models. May or may not be needed later, but not actually doing anything on this app currently.'''
    zoon_id = models.IntegerField(null=True, db_index=True)
    zoon_name = models.CharField(max_length=100, blank=True, db_index=True)


QUESTION_TYPE_CHOICES = (
    ('q', 'question'),
    ('d', 'dropdown')
)


class ReducedResponse_Question(models.Model):
    '''Used for both question and dropdown types'''
    zoon_subject_id = models.IntegerField(db_index=True)
    zoon_workflow_id = models.IntegerField(db_index=True)
    # TODO: add batch or date
    task_id = models.CharField(db_index=True, max_length=4)
    question_type = models.CharField(
        max_length=1, db_index=True, choices=QUESTION_TYPE_CHOICES)
    best_answer = models.TextField()
    best_answer_score = models.FloatField()
    total_votes = models.IntegerField()
    answer_scores = models.JSONField()


class ReducedResponse_Text(models.Model):
    zoon_subject_id = models.IntegerField(db_index=True)
    zoon_workflow_id = models.IntegerField(db_index=True)
    # TODO: add batch or date
    task_id = models.CharField(db_index=True, max_length=4)
    aligned_text = models.JSONField()
    total_votes = models.IntegerField()
    consensus_text = models.TextField()
    consensus_score = models.IntegerField()
    user_ids = models.JSONField()

    # TODO: Need to get individual "something is wrong" responses direct from classifier, since reduce won't handle these well. Or use a different reducer that doesn't, um, reduce
