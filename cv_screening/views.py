from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from core.domain.models import Evaluation
from evaluations.tasks import evaluate_cv_task

def home_view(request):
    return redirect("login")

def custom_404_view(request, exception=None):
    return render(request, "404.html", status=404)

def login_view(request):
    return render(request, "login.html")

@require_http_methods(["GET", "POST"])
def upload_cv_view(request):
    if request.method == "POST":
        cv_file = request.FILES.get("cv")
        if cv_file:
            evaluation = Evaluation.objects.create(cv_file=cv_file)
            evaluate_cv_task.delay(evaluation.id)
            return redirect("evaluation_result", evaluation_id=evaluation.id)
    return render(request, "upload.html")

def evaluation_result_view(request, evaluation_id):
    evaluation = Evaluation.objects.get(id=evaluation_id)
    return render(request, "evaluation_result.html", {"evaluation": evaluation})