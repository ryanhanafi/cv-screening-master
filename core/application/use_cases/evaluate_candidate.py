from core.application.interfaces import (
    IEvaluationRepository,
    IFileParser,
    ILLMService,
    IVectorStore,
)

class EvaluateCandidateUseCase:
    def __init__(
        self,
        evaluation_repository: IEvaluationRepository,
        cv_parser: IFileParser,
        project_parser: IFileParser,
        llm_service: ILLMService,
        vector_store: IVectorStore,
    ):
        self.evaluation_repository = evaluation_repository
        self.cv_parser = cv_parser
        self.project_parser = project_parser
        self.llm_service = llm_service
        self.vector_store = vector_store

    def execute(self, job_id: str):
        job = self.evaluation_repository.get_by_id(job_id)
        job.status = 'processing'
        self.evaluation_repository.update(job)

        try:
            retriever = self.vector_store.get_retriever()

            cv_text = self.cv_parser.parse(job.cv.file.path)
            project_report_text = self.project_parser.parse(job.project_report.file.path)

            cv_result = self.llm_service.evaluate_cv(cv_text, retriever)
            project_result = self.llm_service.evaluate_project(project_report_text, retriever)
            summary_result = self.llm_service.generate_summary(cv_result, project_result)

            # Parse results and update job
            job.cv_match_rate = float(cv_result.split("Match Rate:")[1].split("Feedback:")[0].strip())
            job.cv_feedback = cv_result.split("Feedback:")[1].strip()
            job.project_score = float(project_result.split("Score:")[1].split("Feedback:")[0].strip())
            job.project_feedback = project_result.split("Feedback:")[1].strip()
            job.overall_summary = summary_result.strip()
            job.status = 'completed'
            self.evaluation_repository.update(job)

        except Exception as e:
            job.status = 'failed'
            job.overall_summary = f"An error occurred: {str(e)}"
            self.evaluation_repository.update(job)
