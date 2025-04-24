from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FinancialPeriodViewSet, DividendViewSet, MemberDividendViewSet,
    FeeTypeViewSet, FeeViewSet
)

router = DefaultRouter()
router.register(r'financial-periods', FinancialPeriodViewSet, basename='financial-period')
router.register(r'dividends', DividendViewSet, basename='dividend')
router.register(r'member-dividends', MemberDividendViewSet, basename='member-dividend')  # Fixed typo and basename
router.register(r'fee-types', FeeTypeViewSet, basename='fee-type')
router.register(r'fees', FeeViewSet, basename='fee')

app_name = 'finance'

urlpatterns = [
    path('', include(router.urls)),
]