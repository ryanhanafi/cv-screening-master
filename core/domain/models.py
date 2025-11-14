import uuid
from django.db import models

class UploadedFile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.id)

class EvaluationJob(models.Model):
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_title = models.CharField(max_length=255)
    cv = models.ForeignKey(UploadedFile, related_name='evaluation_cv', on_delete=models.CASCADE)
    project_report = models.ForeignKey(UploadedFile, related_name='evaluation_project_report', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Result fields
    cv_match_rate = models.FloatField(null=True, blank=True)
    cv_feedback = models.TextField(null=True, blank=True)
    project_score = models.FloatField(null=True, blank=True)
    project_feedback = models.TextField(null=True, blank=True)
    overall_summary = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Evaluation {self.id} - {self.status}"