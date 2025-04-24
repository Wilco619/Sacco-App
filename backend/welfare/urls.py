from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WelfareFundViewSet,
    WelfareContributionViewSet,
    WelfareBenefitViewSet,
    WelfareDocumentViewSet
)

router = DefaultRouter()
router.register(r'welfare-funds', WelfareFundViewSet)
router.register(r'contributions', WelfareContributionViewSet, basename='welfare-contribution')
router.register(r'benefits', WelfareBenefitViewSet)
router.register(r'documents', WelfareDocumentViewSet)

app_name = 'welfare'

urlpatterns = [
    path('', include(router.urls)),
]