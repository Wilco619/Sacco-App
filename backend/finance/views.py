from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone
from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend

from .models import FinancialPeriod, Dividend, FeeType, Fee
from .serializers import (
    FinancialPeriodSerializer, DividendSerializer, MemberDividendSerializer,
    FeeTypeSerializer, FeeSerializer
)


class FinancialPeriodViewSet(viewsets.ModelViewSet):
    queryset = FinancialPeriod.objects.all()
    serializer_class = FinancialPeriodSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['period_name', 'description']
    ordering_fields = ['start_date', 'end_date', 'period_name']
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def close_period(self, request, pk=None):
        """
        Action to close a financial period
        """
        period = self.get_object()
        if period.status == 'CLOSED':
            return Response(
                {'detail': 'Period is already closed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        period.status = 'CLOSED'
        period.closed_by = request.user
        period.closed_at = timezone.now()
        period.save()
        
        serializer = self.get_serializer(period)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def current_period(self, request):
        """
        Get the currently active financial period
        """
        today = timezone.now().date()
        try:
            period = FinancialPeriod.objects.get(
                start_date__lte=today,
                end_date__gte=today,
                status='ACTIVE'
            )
            serializer = self.get_serializer(period)
            return Response(serializer.data)
        except FinancialPeriod.DoesNotExist:
            return Response(
                {'detail': 'No active financial period found for today'},
                status=status.HTTP_404_NOT_FOUND
            )


class DividendViewSet(viewsets.ModelViewSet):
    queryset = Dividend.objects.all()
    serializer_class = DividendSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'financial_period']
    search_fields = ['description', 'financial_period__period_name']
    ordering_fields = ['declaration_date', 'payment_date', 'total_amount']
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def approve_dividend(self, request, pk=None):
        """
        Action to approve a dividend
        """
        dividend = self.get_object()
        if dividend.status != 'PROPOSED':
            return Response(
                {'detail': f'Dividend cannot be approved from {dividend.status} status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        dividend.status = 'APPROVED'
        dividend.approval_date = timezone.now().date()
        dividend.approved_by = request.user
        dividend.save()
        
        serializer = self.get_serializer(dividend)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def process_payments(self, request, pk=None):
        """
        Action to start processing dividend payments
        """
        dividend = self.get_object()
        if dividend.status != 'APPROVED':
            return Response(
                {'detail': 'Dividend must be approved before processing payments'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        dividend.status = 'PROCESSING'
        dividend.save()
        
        # Update all pending member dividends to processing
        dividend.member_dividends.filter(payment_status='PENDING').update(
            payment_status='PROCESSING'
        )
        
        serializer = self.get_serializer(dividend)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def mark_paid(self, request, pk=None):
        """
        Action to mark dividend as fully paid
        """
        dividend = self.get_object()
        
        # Check if all member dividends are paid
        unpaid_count = dividend.member_dividends.exclude(payment_status='PAID').count()
        
        if unpaid_count > 0:
            return Response(
                {'detail': f'Cannot mark as paid - {unpaid_count} member payments are still pending'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        dividend.status = 'PAID'
        dividend.payment_date = timezone.now().date()
        dividend.save()
        
        serializer = self.get_serializer(dividend)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def payment_summary(self, request, pk=None):
        """
        Get payment summary statistics for this dividend
        """
        dividend = self.get_object()
        
        summary = {
            'total_members': dividend.member_dividends.count(),
            'total_amount': dividend.total_amount,
            'paid_count': dividend.member_dividends.filter(payment_status='PAID').count(),
            'paid_amount': dividend.member_dividends.filter(payment_status='PAID').aggregate(
                total=Sum('amount')
            )['total'] or 0,
            'pending_count': dividend.member_dividends.filter(payment_status='PENDING').count(),
            'processing_count': dividend.member_dividends.filter(payment_status='PROCESSING').count(),
            'failed_count': dividend.member_dividends.filter(payment_status='FAILED').count(),
        }
        
        return Response(summary)


class MemberDividendViewSet(viewsets.ModelViewSet):
    queryset = Dividend.objects.all()
    serializer_class = MemberDividendSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['payment_status', 'payment_method', 'dividend', 'member']
    search_fields = ['payment_reference', 'member__first_name', 'member__last_name']
    ordering_fields = ['amount', 'processed_date']
    
    def get_queryset(self):
        """
        Filter queryset for regular users to only see their own dividends
        """
        queryset = super().get_queryset()
        user = self.request.user
        
        # If not staff/admin, only show user's own dividends
        if not user.is_staff:
            queryset = queryset.filter(member=user)
            
        return queryset
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def mark_paid(self, request, pk=None):
        """
        Mark a member dividend as paid
        """
        member_dividend = self.get_object()
        
        if member_dividend.payment_status == 'PAID':
            return Response(
                {'detail': 'This dividend payment is already marked as paid'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        member_dividend.payment_status = 'PAID'
        member_dividend.processed_date = timezone.now()
        member_dividend.processed_by = request.user
        
        payment_method = request.data.get('payment_method')
        payment_reference = request.data.get('payment_reference')
        
        if payment_method:
            member_dividend.payment_method = payment_method
            
        if payment_reference:
            member_dividend.payment_reference = payment_reference
            
        member_dividend.save()
        
        # Check if all member dividends are paid to update parent dividend
        all_paid = member_dividend.dividend.member_dividends.exclude(
            payment_status='PAID'
        ).count() == 0
        
        if all_paid and member_dividend.dividend.status != 'PAID':
            member_dividend.dividend.status = 'PAID' 
            member_dividend.dividend.payment_date = timezone.now().date()
            member_dividend.dividend.save()
        
        serializer = self.get_serializer(member_dividend)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_dividends(self, request):
        """
        Get the current user's dividends
        """
        queryset = self.queryset.filter(member=request.user)
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class FeeTypeViewSet(viewsets.ModelViewSet):
    queryset = FeeType.objects.all()
    serializer_class = FeeTypeSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['active', 'calculation_method', 'application_frequency']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'rate_or_amount']
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """
        Toggle the active status of a fee type
        """
        fee_type = self.get_object()
        fee_type.active = not fee_type.active
        fee_type.save()
        
        serializer = self.get_serializer(fee_type)
        return Response(serializer.data)


class FeeViewSet(viewsets.ModelViewSet):
    queryset = Fee.objects.all()
    serializer_class = FeeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'waived', 'fee_type', 'member']
    search_fields = ['description', 'member__first_name', 'member__last_name']
    ordering_fields = ['amount', 'date_charged', 'due_date']
    
    def get_queryset(self):
        """
        Filter queryset for regular users to only see their own fees
        """
        queryset = super().get_queryset()
        user = self.request.user
        
        # If not staff/admin, only show user's own fees
        if not user.is_staff:
            queryset = queryset.filter(member=user)
            
        return queryset
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def mark_paid(self, request, pk=None):
        """
        Mark a fee as paid
        """
        fee = self.get_object()
        
        if fee.status == 'PAID':
            return Response(
                {'detail': 'This fee is already marked as paid'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if fee.waived:
            return Response(
                {'detail': 'This fee has been waived and cannot be marked as paid'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        fee.status = 'PAID'
        fee.date_paid = timezone.now()
        fee.save()
        
        serializer = self.get_serializer(fee)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def waive_fee(self, request, pk=None):
        """
        Waive a fee
        """
        fee = self.get_object()
        
        if fee.status == 'PAID':
            return Response(
                {'detail': 'This fee is already paid and cannot be waived'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reason = request.data.get('waiver_reason')
        if not reason:
            return Response(
                {'detail': 'A waiver reason is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        fee.waived = True
        fee.status = 'WAIVED'
        fee.waiver_reason = reason
        fee.waived_by = request.user
        fee.save()
        
        serializer = self.get_serializer(fee)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_fees(self, request):
        """
        Get the current user's fees
        """
        queryset = self.queryset.filter(member=request.user)
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)