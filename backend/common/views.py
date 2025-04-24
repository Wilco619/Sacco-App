from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q

from .models import AuditLog, Notification, Document, Setting
from .serializers import (
    AuditLogSerializer, NotificationSerializer, 
    DocumentSerializer, SettingSerializer, PublicSettingSerializer
)


class AuditLogViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing audit logs.
    """
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['action', 'entity_type', 'entity_id', 'user__username', 'ip_address']
    ordering_fields = ['timestamp', 'action', 'entity_type']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
            
        # Filter by user if provided
        user_id = self.request.query_params.get('user_id', None)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
            
        # Filter by action if provided
        action = self.request.query_params.get('action', None)
        if action:
            queryset = queryset.filter(action=action)
            
        return queryset


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing notifications.
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'message', 'type']
    ordering_fields = ['created_at', 'priority', 'read']
    
    def get_queryset(self):
        # Users can only see their own notifications unless they're staff
        if self.request.user.is_staff:
            queryset = Notification.objects.all()
            
            # Staff can filter by recipient
            recipient_id = self.request.query_params.get('recipient_id', None)
            if recipient_id:
                queryset = queryset.filter(recipient_id=recipient_id)
        else:
            queryset = Notification.objects.filter(recipient=self.request.user)
        
        # Filter by read status if provided
        read_status = self.request.query_params.get('read', None)
        if read_status is not None:
            is_read = read_status.lower() == 'true'
            queryset = queryset.filter(read=is_read)
            
        # Filter by notification type if provided
        notification_type = self.request.query_params.get('type', None)
        if notification_type:
            queryset = queryset.filter(type=notification_type)
            
        # Filter by priority if provided
        priority = self.request.query_params.get('priority', None)
        if priority:
            queryset = queryset.filter(priority=priority)
            
        return queryset
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        
        # Ensure users can only mark their own notifications as read
        if notification.recipient != request.user and not request.user.is_staff:
            return Response(
                {"detail": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        notification.read = True
        notification.read_at = timezone.now()
        notification.save()
        
        return Response({"status": "notification marked as read"})
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        user = request.user
        notifications = Notification.objects.filter(recipient=user, read=False)
        now = timezone.now()
        
        # Update all unread notifications for the user
        notifications.update(read=True, read_at=now)
        
        return Response({"status": f"marked {notifications.count()} notifications as read"})


class DocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing documents.
    """
    serializer_class = DocumentSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'document_type']
    ordering_fields = ['uploaded_at', 'title', 'document_type']
    
    def get_queryset(self):
        # Users can see public documents and their own unless they're staff
        if self.request.user.is_staff:
            queryset = Document.objects.all()
        else:
            queryset = Document.objects.filter(
                Q(is_public=True) | Q(uploaded_by=self.request.user)
            )
        
        # Filter by document type if provided
        document_type = self.request.query_params.get('document_type', None)
        if document_type:
            queryset = queryset.filter(document_type=document_type)
            
        # Filter by public status if provided
        is_public = self.request.query_params.get('is_public', None)
        if is_public is not None and self.request.user.is_staff:
            public_status = is_public.lower() == 'true'
            queryset = queryset.filter(is_public=public_status)
            
        return queryset
    
    def perform_create(self, serializer):
        # Set the uploaded_by field to the current user
        serializer.save(uploaded_by=self.request.user)
    
    def get_permissions(self):
        # Custom permissions based on action
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]


class SettingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing system settings.
    """
    queryset = Setting.objects.all()
    serializer_class = SettingSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['key', 'description', 'setting_type']
    ordering_fields = ['key', 'setting_type', 'created_at']
    
    def get_permissions(self):
        # Custom permissions based on action
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]
    
    def get_serializer_class(self):
        # Use different serializer for non-admin users
        if not self.request.user.is_staff:
            return PublicSettingSerializer
        return SettingSerializer
    
    def get_queryset(self):
        # Non-staff users can only see public settings
        if not self.request.user.is_staff:
            return Setting.objects.filter(is_public=True)
            
        # Filter by setting type if provided
        setting_type = self.request.query_params.get('setting_type', None)
        if setting_type:
            return Setting.objects.filter(setting_type=setting_type)
            
        return Setting.objects.all()
    
    def perform_create(self, serializer):
        # Set the updated_by field to the current user
        serializer.save(updated_by=self.request.user)
        
    def perform_update(self, serializer):
        # Update the updated_by field when settings are changed
        serializer.save(updated_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def public(self, request):
        """
        Endpoint to fetch public settings only.
        This can be accessed by anyone with auth.
        """
        public_settings = Setting.objects.filter(is_public=True)
        serializer = PublicSettingSerializer(public_settings, many=True)
        return Response(serializer.data)