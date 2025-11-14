# AI CV Screening Backend

This project is a Django-based backend service that automates the initial screening of job applications. It uses a RAG (Retrieval-Augmented Generation) pipeline to evaluate a candidate's CV and project report against a job description and a case study brief.

## Features

-   **RESTful API**: Endpoints for uploading documents, triggering evaluations, and retrieving results.
-   **Asynchronous Processing**: Uses Celery and Redis to handle long-running AI evaluation tasks without blocking API requests.
-   **RAG Pipeline**: Ingests reference documents into a ChromaDB vector store and retrieves them to provide context to an LLM for evaluation.
-   **LLM Chaining**: Uses Langchain to structure the evaluation process into multiple steps (CV evaluation, project report evaluation, final summary).
-   **Secure Endpoints**: API endpoints are protected using JWT authentication.

## Project Structure

-   `cv_screening`: The main Django project directory.
-   `api`: A Django app for the RESTful API (views, serializers, URLs).
-   `evaluations`: A Django app for the data models, Celery tasks, and AI pipeline logic.
-   `documents`: Contains the internal documents used for the RAG system and the ingestion script.
-   `chroma_db`: The directory where the ChromaDB vector store is persisted.
-   `media`: The directory where uploaded CVs and project reports are stored.

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd cv-screening
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    Create a `.env` file in the project root and add your Google API key:
    ```
    GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"
    ```
    **Note:** You need to have a valid Google API key with the Gemini API enabled.

5.  **Apply database migrations:**
    ```bash
    python manage.py migrate
    ```

6.  **Ingest documents into the vector store:**
    This command will read the files in the `documents` directory and ingest them into the ChromaDB vector store.
    ```bash
    python manage.py ingest
    ```

## Running the Application

You will need to run three separate processes in different terminals:

1.  **Start the Redis server:**
    Make sure you have Redis installed and running on your machine.
    ```bash
    redis-server
    ```

2.  **Start the Celery worker:**
    In the project root directory, run:
    ```bash
    celery -A cv_screening worker -l info
    ```

3.  **Start the Django development server:**
    ```bash
    python manage.py runserver
    ```

## API Usage

1.  **Obtain a JWT token:**
    First, you need to create a user to be able to authenticate.
    ```bash
    python manage.py createsuperuser
    ```
    Then, send a POST request to `/api/token/` with the user's credentials to get a JWT token pair.
    ```http
    POST /api/token/
    Content-Type: application/json

    {
        "username": "your-username",
        "password": "your-password"
    }
    ```
    You will receive an `access` token and a `refresh` token.

2.  **Upload documents:**
    Send a `POST` request to `/api/upload/` with the CV and project report as `multipart/form-data`. Include the access token in the `Authorization` header.
    ```http
    POST /api/upload/
    Authorization: Bearer <your-access-token>
    Content-Type: multipart/form-data

    --boundary
    Content-Disposition: form-data; name="file"; filename="cv.pdf"

    <cv.pdf content>
    --boundary
    ```
    You will receive a file ID for each uploaded document.

3.  **Trigger evaluation:**
    Send a `POST` request to `/api/evaluate/` with the job title and the file IDs.
    ```http
    POST /api/evaluate/
    Authorization: Bearer <your-access-token>
    Content-Type: application/json

    {
        "job_title": "Backend Developer",
        "cv_id": "your-cv-id",
        "project_report_id": "your-project-report-id"
    }
    ```
    You will receive a job ID and a `queued` status.

4.  **Retrieve results:**
    Send a `GET` request to `/api/result/<job_id>/` to check the status and retrieve the results once the evaluation is complete.
    ```http
    GET /api/result/your-job-id/
    Authorization: Bearer <your-access-token>
    ```

## Design Choices

-   **Django**: A robust and scalable framework for building the backend service.
-   **Django Rest Framework**: A powerful and flexible toolkit for building Web APIs in Django.
-   **Celery & Redis**: The standard choice for handling asynchronous tasks in Django, ensuring that the API remains responsive during long-running AI evaluations.
-   **ChromaDB**: A simple and easy-to-use vector store that can be run locally, making it ideal for this project.
-   **Langchain**: Simplifies the development of LLM-powered applications by providing tools for chaining, RAG, and more.
-   **Google Gemini**: A powerful and versatile LLM that is well-suited for the evaluation tasks in this project.
-   **Clean Architecture**: The project is structured to separate concerns, with the API, data models, and AI logic in different apps. This makes the codebase easier to maintain and extend.
-   **JWT Authentication**: Provides a secure and stateless way to authenticate API requests.
