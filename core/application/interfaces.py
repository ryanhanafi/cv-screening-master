from abc import ABC, abstractmethod

class IVectorStore(ABC):
    @abstractmethod
    def get_retriever(self):
        pass

class ILLMService(ABC):
    @abstractmethod
    def evaluate_cv(self, cv_content: str, retriever):
        pass

    @abstractmethod
    def evaluate_project(self, project_content: str, retriever):
        pass

    @abstractmethod
    def generate_summary(self, cv_evaluation: str, project_evaluation: str):
        pass

class IFileParser(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> str:
        pass

class IEvaluationRepository(ABC):
    @abstractmethod
    def get_by_id(self, job_id: str):
        pass

    @abstractmethod
    def update(self, job):
        pass
