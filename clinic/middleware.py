from django.utils import timezone
from django.shortcuts import redirect
from datetime import datetime

class TrialMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        expires = request.session.get('trial_expires')
        if expires:
            if timezone.now() > datetime.fromisoformat(expires):
                return redirect('/assinatura-expirada/')
        return self.get_response(request)
