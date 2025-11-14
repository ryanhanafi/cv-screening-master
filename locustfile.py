"""
Locust load testing untuk CV Screening API
Jalankan dengan: locust -f locustfile.py --host=http://localhost:8000
"""

from locust import HttpUser, task, between, events
from locust.contrib.fasthttp import FastHttpUser
import json
import uuid
import random
from io import BytesIO


class CVScreeningUser(HttpUser):
    """Simulates typical user behavior on CV Screening API."""
    wait_time = between(1, 5)
    
    def on_start(self):
        """Initialize with test credentials (adjust if auth required)."""
        self.user_token = None
        # Uncomment if using token auth:
        # self.login()

    def login(self):
        """Authenticate user (if required)."""
        response = self.client.post('/api/login/', json={
            'username': 'testuser',
            'password': 'testpass'
        })
        if response.status_code == 200:
            data = response.json()
            self.user_token = data.get('token')

    @task(3)
    def upload_cv(self):
        """Upload CV file (3x more frequent than evaluate)."""
        # Create dummy PDF content
        pdf_content = b'%PDF-1.4\n%test CV content\n'
        
        with self.client.post(
            '/api/upload/',
            files={'file': ('test_cv.pdf', BytesIO(pdf_content), 'application/pdf')},
            headers=self.get_auth_headers(),
            catch_response=True
        ) as response:
            if response.status_code in [201, 400, 413, 429]:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(1)
    def start_evaluation(self):
        """Trigger evaluation job."""
        payload = {
            'job_title': f'Test Job {random.randint(1, 100)}',
            'cv_id': str(uuid.uuid4()),
            'project_report_id': str(uuid.uuid4())
        }
        
        with self.client.post(
            '/api/evaluate/',
            json=payload,
            headers={**self.get_auth_headers(), 'Content-Type': 'application/json'},
            catch_response=True
        ) as response:
            if response.status_code in [202, 400, 429]:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(2)
    def get_evaluation_result(self):
        """Check evaluation job result."""
        job_id = str(uuid.uuid4())  # In real scenario, use actual job ID
        
        with self.client.get(
            f'/api/result/{job_id}/',
            headers=self.get_auth_headers(),
            catch_response=True
        ) as response:
            if response.status_code in [200, 404, 429]:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    def get_auth_headers(self):
        """Return authorization headers."""
        if self.user_token:
            return {'Authorization': f'Bearer {self.user_token}'}
        return {}


class BurstUser(HttpUser):
    """User that sends burst requests to test throttling."""
    wait_time = between(0, 1)  # Minimal wait
    
    @task
    def upload_burst(self):
        """Rapid-fire upload requests."""
        for _ in range(10):
            pdf_content = b'%PDF-1.4\nTest\n'
            self.client.post(
                '/api/upload/',
                files={'file': ('test.pdf', BytesIO(pdf_content), 'application/pdf')},
                catch_response=True
            )


# Event handlers for monitoring
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, response, context, exception, **kwargs):
    """Log throttle hits (429 responses)."""
    if response and response.status_code == 429:
        print(f"⚠️  THROTTLED: {request_type} {name} (response_time: {response_time}ms)")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Print test start info."""
    print("\n🚀 Load test started")
    print("Monitor 429 (Too Many Requests) responses for throttle validation")
    print("Expected throttle limits:")
    print("  - /api/upload/ : 5 req/min")
    print("  - /api/evaluate/ : 2 req/min")
    print()


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print test summary."""
    print("\n✅ Load test completed")
    print(f"Total requests: {environment.stats.total.num_requests}")
    print(f"Failed requests: {environment.stats.total.num_failures}")
    print(f"Avg response time: {environment.stats.total.avg_response_time:.0f}ms")
