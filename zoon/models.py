from django.db import models

class ReducedResponse_Question(models.Model):
    zoon_subject_id = models.IntegerField(db_index=True)
    zoon_workflow_id = models.IntegerField(db_index=True)
    task_id = models.CharField(db_index=True, max_length=4)
    best_answer = models.TextField()
    best_answer_score = models.FloatField()
    total_votes = models.IntegerField()
    answer_scores = models.JSONField()
