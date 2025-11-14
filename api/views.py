from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import UploadedFileSerializer, EvaluationJobSerializer, EvaluationRequestSerializer
from core.domain.models import UploadedFile, EvaluationJob
from evaluations.tasks import evaluate_documents
from core.throttles import CVUploadRateThrottle, EvaluationRateThrottle

class UploadView(generics.CreateAPIView):
    queryset = UploadedFile.objects.all()
    serializer_class = UploadedFileSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [CVUploadRateThrottle]

class EvaluateView(generics.GenericAPIView):
    serializer_class = EvaluationRequestSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [EvaluationRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # This is where the async task will be triggered
            job = EvaluationJob.objects.create(
                job_title=serializer.validated_data['job_title'],
                cv_id=serializer.validated_data['cv_id'],
                project_report_id=serializer.validated_data['project_report_id'],
            )
            evaluate_documents.delay(job.id)
            return Response({'id': job.id, 'status': job.status}, status=status.HTTP_202_ACCEPTED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResultView(generics.RetrieveAPIView):
    queryset = EvaluationJob.objects.all()
    serializer_class = EvaluationJobSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'job_id'
    permission_classes = [IsAuthenticated]