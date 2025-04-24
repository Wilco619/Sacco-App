from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or admin users to access it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin users can access any object
        if request.user.is_staff:
            return True
            
        # Check if the object has an owner field (adjust the attribute name as needed)
        if hasattr(obj, 'uploaded_by'):
            return obj.uploaded_by == request.user
        elif hasattr(obj, 'recipient'):
            return obj.recipient == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
            
        # If no owner field is found, deny permission
        return False


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow administrators to edit, but allow read-only for authenticated users.
    """
    
    def has_permission(self, request, view):
        # Read permissions are allowed for authenticated users
        if request.method in permissions.SAFE_METHODS and request.user.is_authenticated:
            return True
            
        # Write permissions are only allowed for admin users
        return request.user.is_staff


class IsPublicOrOwnerOrAdmin(permissions.BasePermission):
    """
    Permission to allow access to public items, owners, or admins.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin users can access any object
        if request.user.is_staff:
            return True
            
        # Check if the object is public
        if hasattr(obj, 'is_public') and obj.is_public:
            return True
            
        # Check if the object has an owner field
        if hasattr(obj, 'uploaded_by'):
            return obj.uploaded_by == request.user
            
        # If no conditions are met, deny permission
        return False