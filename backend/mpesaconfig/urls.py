from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MPesaViewSet

router = DefaultRouter()
router.register('', MPesaViewSet, basename='mpesa')

app_name = 'mpesaconfig'

urlpatterns = [
    path('', include(router.urls)),
    # These are automatically included by the router:
    # POST /initiate_payment/
    # POST /callback/
    # POST /query_status/
]
