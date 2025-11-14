from celery import shared_task
from dotenv import load_dotenv

from core.application.use_cases.evaluate_candidate import EvaluateCandidateUseCase
from core.infra.persistence.django_repository import DjangoEvaluationRepository
from core.infra.file_parser import PdfParser
from core.infra.llm.google import GoogleLLMService
from core.infra.vector_store.chroma import ChromaVectorStore

load_dotenv()

@shared_task(rate_limit='5/m', time_limit=300)
def evaluate_documents(job_id):
    """
    Celery task to evaluate a candidate's documents.
    This task acts as the Composition Root for the evaluation use case.
    """
    # 1. Initialize concrete implementations
    evaluation_repo = DjangoEvaluationRepository()
    pdf_parser = PdfParser()
    llm_service = GoogleLLMService()
    vector_store = ChromaVectorStore()

    # 2. Initialize the use case with concrete dependencies
    use_case = EvaluateCandidateUseCase(
        evaluation_repository=evaluation_repo,
        cv_parser=pdf_parser,
        project_parser=pdf_parser,
        llm_service=llm_service,
        vector_store=vector_store,
    )

    # 3. Execute the use case
    use_case.execute(job_id)