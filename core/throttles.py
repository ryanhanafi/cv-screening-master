from rest_framework.throttling import SimpleRateThrottle


class CVUploadRateThrottle(SimpleRateThrottle):
    """Rate throttle for CV/file uploads. Scope maps to REST_FRAMEWORK DEFAULT_THROTTLE_RATES 'upload_cv'."""
    scope = 'upload_cv'


class EvaluationRateThrottle(SimpleRateThrottle):
    """Rate throttle for evaluation job creation. Scope maps to REST_FRAMEWORK DEFAULT_THROTTLE_RATES 'start_evaluation'."""
    scope = 'start_evaluation'
