from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MemberViewSet, SavingsViewSet, LoanViewSet, 
    ShareViewSet, 
    MemberGroupViewSet
)

router = DefaultRouter()
# Explicitly set the basename for members
router.register('members', MemberViewSet, basename='accounts-member')
router.register('savings', SavingsViewSet, basename='saving')
router.register('loans', LoanViewSet, basename='loan')
router.register('shares', ShareViewSet, basename='shares')
router.register('groups', MemberGroupViewSet, basename='group')

app_name = 'accounts'

urlpatterns = [
    path('', include(router.urls)),
    path('my_shares/', ShareViewSet.as_view({'get': 'my_shares'}), name='my_shares'),
]