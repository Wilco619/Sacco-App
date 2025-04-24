# users/permissions.py
from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    """
    Custom permission to only allow admin users to access the view.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.user_type == 'ADMIN'


class IsSelfOrAdmin(BasePermission):
    """
    Custom permission to only allow users to edit their own profile
    or admin users to edit any profile.
    """
    def has_object_permission(self, request, view, obj):
        # Admin can do anything
        if request.user.user_type == 'ADMIN':
            return True
            
        # Users can only modify their own data
        return obj.id == request.user.id


class CanChangeRestrictedFields(BasePermission):
    """
    Custom permission to restrict non-admin users from changing certain fields.
    """
    def has_permission(self, request, view):
        # Check if user is admin
        if request.user.user_type == 'ADMIN':
            return True
            
        # For non-admins, check if they're trying to change restricted fields
        restricted_fields = ['id_number', 'phone_number', 'email']
        for field in restricted_fields:
            if field in request.data:
                return False
        return True