from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('', views.UserViewSet, basename='user')  # Changed from r'' to 'users'
router.register('profiles', views.ProfileViewSet, basename='profile')

urlpatterns = [
    path('', include(router.urls)),
]