from core.application.interfaces import IEvaluationRepository
from core.domain.models import EvaluationJob

class DjangoEvaluationRepository(IEvaluationRepository):
    def get_by_id(self, job_id: str):
        return EvaluationJob.objects.get(id=job_id)

    def update(self, job):
        job.save()
