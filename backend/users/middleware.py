# users/middleware.py
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from rest_framework import status

class MemberDocumentVerificationMiddleware:
    """
    Middleware to ensure members have uploaded required documents
    """
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        # Skip middleware if user is not authenticated or is admin
        if not request.user.is_authenticated:
            return None
            
        if request.user.user_type == 'ADMIN':
            return None
            
        # Skip middleware for certain URLs (authentication, profile update, etc.)
        exempt_urls = [
            reverse('token_obtain_pair'),
            reverse('token_refresh'),
            '/api/users/profiles/me/',
            '/api/users/change_password/',
        ]
        
        if any(request.path.startswith(url) for url in exempt_urls):
            return None
            
        # Check if all required documents are uploaded
        profile = request.user.profile
        if (not profile.id_front_image or 
            not profile.id_back_image or 
            not profile.passport_photo or 
            not profile.signature):
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # For AJAX requests
                return JsonResponse({
                    'status': 'error',
                    'message': 'Please upload all required documents'
                }, status=403)
            else:
                messages.warning(
                    request, 
                    'Please upload all required documents to access all features.'
                )
                return redirect('profile_update')  # Redirect to profile update page
                
        return None

class RegistrationPaymentMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Exclude auth endpoints and registration payment endpoint
        excluded_paths = [
            '/api/auth/', 
            '/api/members/registration-payment/',
            '/api/members/registration-status/'
        ]
        
        if any(request.path.startswith(path) for path in excluded_paths):
            return None

        if request.user.is_authenticated:
            try:
                member = request.user.member
                if member.needs_registration_payment:
                    return JsonResponse({
                        'error': 'Registration payment required',
                        'registration_required': True,
                        'message': 'Please pay registration fee of 1000 KSH to activate your membership'
                    }, status=status.HTTP_402_PAYMENT_REQUIRED)
            except:
                pass
        return None