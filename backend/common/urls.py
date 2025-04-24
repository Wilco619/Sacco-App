from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'audit-logs', views.AuditLogViewSet, basename='audit-log')
router.register(r'notifications', views.NotificationViewSet, basename='notification')
router.register(r'documents', views.DocumentViewSet, basename='document')
router.register(r'settings', views.SettingViewSet, basename='setting')

urlpatterns = [
    path('', include(router.urls)),
]