from langchain_google_genai import GoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from core.application.interfaces import ILLMService

class GoogleLLMService(ILLMService):
    def __init__(self, model_name="gemini-pro"):
        self.llm = GoogleGenerativeAI(model=model_name)

    def evaluate_cv(self, cv_content: str, retriever):
        prompt = PromptTemplate(
            template="""
            Based on the following job description and scoring rubric, evaluate the candidate's CV.
            
            Job Description: {job_description}
            
            CV Scoring Rubric: {cv_rubric}
            
            Candidate CV: {cv_text}
            
            Provide a match rate (0.0 to 1.0) and feedback.
            Format your response as:
            Match Rate: [rate]
            Feedback: [feedback]
            """,
            input_variables=["job_description", "cv_rubric", "cv_text"]
        )
        
        job_description_docs = retriever.get_relevant_documents("Backend Developer Job Description")
        cv_rubric_docs = retriever.get_relevant_documents("CV Evaluation Scoring Rubric")
        
        chain = prompt | self.llm | StrOutputParser()
        result = chain.invoke({
            "job_description": " ".join([doc.page_content for doc in job_description_docs]),
            "cv_rubric": " ".join([doc.page_content for doc in cv_rubric_docs]),
            "cv_text": cv_content
        })
        return result

    def evaluate_project(self, project_content: str, retriever):
        prompt = PromptTemplate(
            template="""
            Based on the following case study brief and scoring rubric, evaluate the candidate's project report.
            
            Case Study Brief: {case_study_brief}
            
            Project Scoring Rubric: {project_rubric}
            
            Candidate Project Report: {project_report_text}
            
            Provide a score (1.0 to 5.0) and feedback.
            Format your response as:
            Score: [score]
            Feedback: [feedback]
            """,
            input_variables=["case_study_brief", "project_rubric", "project_report_text"]
        )
        
        case_study_docs = retriever.get_relevant_documents("Case Study Brief")
        project_rubric_docs = retriever.get_relevant_documents("Project Deliverable Evaluation Scoring Rubric")
        
        chain = prompt | self.llm | StrOutputParser()
        result = chain.invoke({
            "case_study_brief": " ".join([doc.page_content for doc in case_study_docs]),
            "project_rubric": " ".join([doc.page_content for doc in project_rubric_docs]),
            "project_report_text": project_content
        })
        return result

    def generate_summary(self, cv_evaluation: str, project_evaluation: str):
        prompt = PromptTemplate(
            template="""
            Based on the CV evaluation and project report evaluation, provide a concise overall summary of the candidate.
            
            CV Evaluation: {cv_evaluation}
            
            Project Report Evaluation: {project_evaluation}
            
            Provide a 3-5 sentence summary.
            """,
            input_variables=["cv_evaluation", "project_evaluation"]
        )
        
        chain = prompt | self.llm | StrOutputParser()
        result = chain.invoke({
            "cv_evaluation": cv_evaluation,
            "project_evaluation": project_evaluation
        })
        return result
