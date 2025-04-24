from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LoanViewSet, GuarantorViewSet, LoanRepaymentViewSet,
    PenaltyTypeViewSet, PenaltyViewSet
)

router = DefaultRouter()
router.register(r'loans', LoanViewSet, basename="loans")
router.register(r'guarantors', GuarantorViewSet, basename="guarantors")
router.register(r'repayments', LoanRepaymentViewSet, basename="repayments")
router.register(r'penalty-types', PenaltyTypeViewSet, basename="penalty-types")
router.register(r'penalties', PenaltyViewSet, basename="penalties")

urlpatterns = [
    path('', include(router.urls)),
]
