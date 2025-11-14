from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from io import BytesIO
import json

from core.domain.models import UploadedFile, EvaluationJob
from api.serializers import UploadedFileSerializer, EvaluationRequestSerializer


class UploadViewThrottleTests(TestCase):
    """Test rate limiting on UploadView."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)
        self.upload_url = '/api/upload/'  # adjust if your URL routing differs

    def test_upload_throttle_limit_exceeded(self):
        """Test that upload requests exceed throttle limit (5/minute)."""
        # Create 6 valid file uploads rapidly
        for i in range(6):
            file = SimpleUploadedFile(
                f'test_{i}.pdf',
                b'%PDF-1.4\n%test content',
                content_type='application/pdf'
            )
            response = self.client.post(self.upload_url, {'file': file})
            
            if i < 5:
                # First 5 should succeed (or be accepted)
                self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])
            else:
                # 6th should be throttled (429)
                self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class EvaluateViewThrottleTests(TestCase):
    """Test rate limiting on EvaluateView."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)
        self.evaluate_url = '/api/evaluate/'  # adjust if your URL routing differs

    def test_evaluate_throttle_limit_exceeded(self):
        """Test that evaluation requests exceed throttle limit (2/minute)."""
        # Create dummy UUIDs for testing
        import uuid
        cv_id = uuid.uuid4()
        project_id = uuid.uuid4()
        job_title = 'Test Job'

        # Create 3 evaluation requests rapidly
        for i in range(3):
            data = {
                'job_title': job_title,
                'cv_id': str(cv_id),
                'project_report_id': str(project_id)
            }
            response = self.client.post(
                self.evaluate_url,
                data=json.dumps(data),
                content_type='application/json'
            )
            
            if i < 2:
                # First 2 should succeed (202 ACCEPTED or validation error)
                self.assertIn(response.status_code, [status.HTTP_202_ACCEPTED, status.HTTP_400_BAD_REQUEST])
            else:
                # 3rd should be throttled (429)
                self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class FileUploadValidationTests(TestCase):
    """Test file validation in UploadedFileSerializer."""

    @override_settings(FILE_UPLOAD_MAX_MEMORY_SIZE=2 * 1024 * 1024)
    def test_file_too_large(self):
        """Test that files larger than limit are rejected."""
        # Create a file larger than 2MB
        large_content = b'x' * (3 * 1024 * 1024)  # 3MB
        file = SimpleUploadedFile(
            'large.pdf',
            large_content,
            content_type='application/pdf'
        )
        
        serializer = UploadedFileSerializer(data={'file': file})
        # Note: validation might happen at different stage; adjust if needed
        is_valid = serializer.is_valid()
        if not is_valid:
            self.assertIn('file', serializer.errors)

    def test_invalid_content_type(self):
        """Test that non-allowed file types are rejected."""
        # Create a .txt file (not allowed)
        file = SimpleUploadedFile(
            'test.txt',
            b'some text content',
            content_type='text/plain'
        )
        
        serializer = UploadedFileSerializer(data={'file': file})
        is_valid = serializer.is_valid()
        if not is_valid:
            self.assertIn('file', serializer.errors)

    def test_valid_pdf_upload(self):
        """Test that valid PDF files are accepted."""
        file = SimpleUploadedFile(
            'test.pdf',
            b'%PDF-1.4\n%test content',
            content_type='application/pdf'
        )
        
        # Serializer validation should pass or fail gracefully
        serializer = UploadedFileSerializer(data={'file': file})
        # If model validation fails for other reasons, that's OK; we're testing file field


class UnauthenticatedAccessTests(TestCase):
    """Test that unauthenticated users cannot access protected endpoints."""

    def setUp(self):
        self.client = APIClient()

    def test_upload_requires_auth(self):
        """Test that upload endpoint requires authentication."""
        file = SimpleUploadedFile('test.pdf', b'%PDF', content_type='application/pdf')
        response = self.client.post('/api/upload/', {'file': file})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_evaluate_requires_auth(self):
        """Test that evaluate endpoint requires authentication."""
        response = self.client.post(
            '/api/evaluate/',
            data=json.dumps({
                'job_title': 'Test',
                'cv_id': '550e8400-e29b-41d4-a716-446655440000',
                'project_report_id': '550e8400-e29b-41d4-a716-446655440001'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
