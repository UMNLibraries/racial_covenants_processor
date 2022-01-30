from django.db import models

class ReducedResponse_Question(models.Model):
    zoon_subject_id = models.IntegerField(db_index=True)
    zoon_workflow_id = models.IntegerField(db_index=True)
    # TODO: add batch or date
    task_id = models.CharField(db_index=True, max_length=4)
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
