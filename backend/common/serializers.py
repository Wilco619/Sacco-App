from rest_framework import serializers
from .models import AuditLog, Notification, Document, Setting


class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'user_name', 'action', 'entity_type', 
            'entity_id', 'timestamp', 'ip_address', 'user_agent', 'details'
        ]
        read_only_fields = ['timestamp']
    
    def get_user_name(self, obj):
        if obj.user:
            return obj.user.get_full_name()
        return None


class NotificationSerializer(serializers.ModelSerializer):
    recipient_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'recipient', 'recipient_name', 'type', 'title', 
            'message', 'created_at', 'read', 'read_at', 'priority', 'link'
        ]
        read_only_fields = ['created_at']
    
    def get_recipient_name(self, obj):
        return obj.recipient.get_full_name()


class DocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id', 'title', 'document_type', 'file', 'file_url', 'description',
            'uploaded_by', 'uploaded_by_name', 'uploaded_at', 'is_public', 'version'
        ]
        read_only_fields = ['uploaded_at']
    
    def get_uploaded_by_name(self, obj):
        if obj.uploaded_by:
            return obj.uploaded_by.get_full_name()
        return None
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
        return None


class SettingSerializer(serializers.ModelSerializer):
    updated_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Setting
        fields = [
            'id', 'key', 'value', 'data_type', 'setting_type', 'description',
            'is_public', 'created_at', 'updated_at', 'updated_by', 'updated_by_name'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_updated_by_name(self, obj):
        if obj.updated_by:
            return obj.updated_by.get_full_name()
        return None


class PublicSettingSerializer(serializers.ModelSerializer):
    """Serializer for public settings only"""
    
    class Meta:
        model = Setting
        fields = ['key', 'value', 'data_type', 'setting_type', 'description']