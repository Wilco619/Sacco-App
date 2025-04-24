from datetime import timedelta
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone
from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.parsers import MultiPartParser, FormParser
from dateutil.relativedelta import relativedelta

from mpesaconfig.models import Transaction
from mpesaconfig.welfare_payments import WelfarePaymentHandler
from .models import WelfareFund, WelfareContribution, WelfareBenefit, WelfareDocument
from .serializers import (
    WelfareFundSerializer, WelfareContributionSerializer,
    WelfareBenefitSerializer, WelfareDocumentSerializer, WelfareDocumentDetailSerializer, WelfarePaymentSerializer
)

import logging
logger = logging.getLogger('welfare')

class WelfareFundViewSet(viewsets.ModelViewSet):
    queryset = WelfareFund.objects.all()
    serializer_class = WelfareFundSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'contribution_frequency']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'date_established', 'total_amount']
    
    def get_permissions(self):
        """
        Ensure only staff can create, update, or delete welfare funds
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'toggle_status']:
            return [IsAdminUser()]
        return super().get_permissions()
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def toggle_status(self, request, pk=None):
        """
        Toggle the active/inactive status of a welfare fund
        """
        fund = self.get_object()
        
        if fund.status == 'ACTIVE':
            fund.status = 'INACTIVE'
        else:
            fund.status = 'ACTIVE'
            
        fund.save()
        
        serializer = self.get_serializer(fund)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def contributions_summary(self, request, pk=None):
        """
        Get summary of contributions for this fund
        """
        fund = self.get_object()
        
        total_confirmed = fund.contributions.filter(status='CONFIRMED').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        total_pending = fund.contributions.filter(status='PENDING').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        contribution_count = fund.contributions.filter(status='CONFIRMED').count()
        
        contributors_count = fund.contributions.filter(
            status='CONFIRMED'
        ).values('member').distinct().count()
        
        summary = {
            'fund_name': fund.name,
            'total_amount': fund.total_amount,
            'total_confirmed_contributions': total_confirmed,
            'total_pending_contributions': total_pending,
            'contribution_count': contribution_count,
            'contributors_count': contributors_count
        }
        
        return Response(summary)
    
    @action(detail=True, methods=['get'])
    def benefits_summary(self, request, pk=None):
        """
        Get summary of benefits paid out from this fund
        """
        fund = self.get_object()
        
        total_approved = fund.benefits.filter(status='APPROVED').aggregate(
            total=Sum('approved_amount')
        )['total'] or 0
        
        total_disbursed = fund.benefits.filter(status='DISBURSED').aggregate(
            total=Sum('approved_amount')
        )['total'] or 0
        
        benefits_count = fund.benefits.filter(
            status__in=['APPROVED', 'DISBURSED']
        ).count()
        
        beneficiaries_count = fund.benefits.filter(
            status__in=['APPROVED', 'DISBURSED']
        ).values('member').distinct().count()
        
        by_reason = {}
        for reason_choice, _ in WelfareBenefit.REASON_CHOICES:
            reason_total = fund.benefits.filter(
                status__in=['APPROVED', 'DISBURSED'], 
                reason=reason_choice
            ).aggregate(total=Sum('approved_amount'))['total'] or 0
            
            by_reason[reason_choice] = reason_total
        
        summary = {
            'fund_name': fund.name,
            'total_amount': fund.total_amount,
            'total_approved_benefits': total_approved,
            'total_disbursed_benefits': total_disbursed,
            'benefits_count': benefits_count,
            'beneficiaries_count': beneficiaries_count,
            'benefits_by_reason': by_reason
        }
        
        return Response(summary)


class WelfareContributionViewSet(viewsets.ModelViewSet):
    serializer_class = WelfareContributionSerializer
    permission_classes = [IsAuthenticated]
    payment_handler = WelfarePaymentHandler()

    def get_queryset(self):
        """Filter queryset to show only user's contributions"""
        return WelfareContribution.objects.filter(
            member=self.request.user
        ).select_related('welfare_fund')

    @action(detail=False, methods=['post'])
    def initiate_payment(self, request):
        """Initiate welfare payment"""
        logger.info(f"Payment initiation started for user: {request.user.id_number}")
        try:
            phone_number = request.data.get('phone_number')
            amount = request.data.get('amount', 300)

            # Validate phone number
            if not phone_number:
                return Response({
                    'success': False,
                    'message': 'Phone number is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Format phone number
            phone_number = self.format_phone_number(phone_number)

            # Get active welfare fund and validate
            welfare_fund = WelfareFund.objects.filter(status='ACTIVE').first()
            if not welfare_fund:
                return Response({
                    'success': False,
                    'message': 'No active welfare fund found'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check monthly contribution
            if amount != welfare_fund.minimum_contribution:
                return Response({
                    'success': False,
                    'message': f'Required contribution amount is {welfare_fund.minimum_contribution}'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check if already contributed this month
            current_month = timezone.now()
            has_contributed = WelfareContribution.objects.filter(
                member=request.user,
                contribution_date__year=current_month.year,
                contribution_date__month=current_month.month,
                status='CONFIRMED'
            ).exists()

            if has_contributed:
                return Response({
                    'success': False,
                    'message': 'Already contributed this month'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Initialize payment using handler
            payment_response = self.payment_handler.initiate_payment(
                phone=phone_number,
                amount=amount,
                user=request.user,
                welfare_fund=welfare_fund
            )

            logger.info(f"Payment initiated: {payment_response}")
            return Response(payment_response)

        except Exception as e:
            logger.exception("Payment initiation failed")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def my_contributions(self, request):
        """Get user's contributions history"""
        try:
            contributions = self.get_queryset().order_by('-contribution_date')

            # Get payment status from handler
            payment_status = self.payment_handler.get_payment_status({
                'user': request.user
            })

            data = {
                'contributions': WelfareContributionSerializer(contributions, many=True).data,
                'can_contribute': payment_status.get('can_contribute', True),
                'next_contribution_date': payment_status.get('next_contribution_due'),
                'monthly_amount': 300,  # This should come from settings or welfare fund
                'last_contribution_date': payment_status.get('last_contribution_month')
            }

            return Response(data)

        except Exception as e:
            logger.exception("Failed to fetch contributions")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def check_payment_status(self, request):
        """Check welfare payment status"""
        try:
            checkout_request_id = request.data.get('checkout_request_id')
            if not checkout_request_id:
                return Response({
                    'success': False,
                    'message': 'Checkout request ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get transaction
            transaction = Transaction.objects.filter(
                checkout_request_id=checkout_request_id,
                user=request.user,
                payment_type='WELFARE'
            ).first()

            if not transaction:
                return Response({
                    'success': False,
                    'message': 'Transaction not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # Check status using handler
            status_response = self.payment_handler.get_payment_status(transaction)

            # If payment is completed, process the contribution
            if transaction.status == 'COMPLETED' and status_response.get('success'):
                contribution = WelfareContribution.objects.filter(
                    reference_number=checkout_request_id
                ).first()

                if contribution:
                    return Response({
                        'success': True,
                        'status': 'COMPLETED',
                        'contribution_id': contribution.id,
                        'amount': str(contribution.amount),
                        'contribution_date': contribution.contribution_date.isoformat()
                    })

            return Response(status_response)

        except Exception as e:
            logger.exception("Payment status check failed")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def format_phone_number(self, phone_number):
        """Format phone number to standard format"""
        # Remove any non-digit characters
        phone_number = ''.join(filter(str.isdigit, phone_number))
        
        # Convert to international format
        if phone_number.startswith('0'):
            phone_number = f'254{phone_number[1:]}'
        elif not phone_number.startswith('254'):
            phone_number = f'254{phone_number}'
            
        return phone_number


class WelfareBenefitViewSet(viewsets.ModelViewSet):
    queryset = WelfareBenefit.objects.all()
    serializer_class = WelfareBenefitSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'welfare_fund', 'member', 'reason']
    search_fields = ['other_reason', 'member__first_name', 'member__last_name']
    ordering_fields = ['application_date', 'amount', 'approved_amount']
    
    def get_queryset(self):
        """
        Filter queryset for regular users to only see their own benefits
        """
        queryset = super().get_queryset()
        user = self.request.user
        
        # If not staff/admin, only show user's own benefits
        if not user.is_staff:
            queryset = queryset.filter(member=user)
            
        return queryset
    
    def perform_create(self, serializer):
        """
        Set the member to the current user if not specified and user is not staff
        """
        if not self.request.user.is_staff and 'member_id' not in self.request.data:
            serializer.save(member=self.request.user)
        else:
            serializer.save()
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def review(self, request, pk=None):
        """
        Mark a benefit application as under review
        """
        benefit = self.get_object()
        
        if benefit.status != 'APPLIED':
            return Response(
                {'detail': f'Benefit application is already {benefit.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        benefit.status = 'UNDER_REVIEW'
        benefit.reviewed_by = request.user
        benefit.save()
        
        serializer = self.get_serializer(benefit)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def approve(self, request, pk=None):
        """
        Approve a benefit application
        """
        benefit = self.get_object()
        
        if benefit.status not in ['APPLIED', 'UNDER_REVIEW']:
            return Response(
                {'detail': f'Benefit application cannot be approved from {benefit.status} status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        approved_amount = request.data.get('approved_amount')
        if not approved_amount:
            return Response(
                {'detail': 'Approved amount is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            approved_amount = float(approved_amount)
        except ValueError:
            return Response(
                {'detail': 'Approved amount must be a valid number'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if fund has sufficient balance
        fund = benefit.welfare_fund
        if fund.total_amount < approved_amount:
            return Response(
                {'detail': 'Fund has insufficient balance for this benefit payment'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        benefit.status = 'APPROVED'
        benefit.approved_amount = approved_amount
        benefit.approval_date = timezone.now()
        benefit.approved_by = request.user
        benefit.save()
        
        serializer = self.get_serializer(benefit)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def disburse(self, request, pk=None):
        """
        Mark a benefit as disbursed
        """
        benefit = self.get_object()
        
        if benefit.status != 'APPROVED':
            return Response(
                {'detail': 'Only approved benefits can be disbursed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if fund has sufficient balance (double check)
        fund = benefit.welfare_fund
        if fund.total_amount < benefit.approved_amount:
            return Response(
                {'detail': 'Fund has insufficient balance for this benefit payment'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        benefit.status = 'DISBURSED'
        benefit.disbursement_date = timezone.now()
        benefit.save()
        
        # Update the fund's total amount
        fund.total_amount -= benefit.approved_amount
        fund.save()
        
        serializer = self.get_serializer(benefit)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def reject(self, request, pk=None):
        """
        Reject a benefit application
        """
        benefit = self.get_object()
        
        if benefit.status not in ['APPLIED', 'UNDER_REVIEW']:
            return Response(
                {'detail': f'Benefit application cannot be rejected from {benefit.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        rejection_reason = request.data.get('rejection_reason')
        if not rejection_reason:
            return Response(
                {'detail': 'Rejection reason is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        benefit.status = 'REJECTED'
        benefit.rejection_reason = rejection_reason
        benefit.reviewed_by = request.user
        benefit.save()
        
        serializer = self.get_serializer(benefit)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_benefits(self, request):
        """
        Get current user's benefit applications
        """
        queryset = self.queryset.filter(member=request.user)
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class WelfareDocumentViewSet(viewsets.ModelViewSet):
    queryset = WelfareDocument.objects.all()
    serializer_class = WelfareDocumentSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['benefit']
    search_fields = ['title', 'description']
    ordering_fields = ['uploaded_at']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return WelfareDocumentDetailSerializer
        return WelfareDocumentSerializer
    
    def get_queryset(self):
        """
        Filter queryset for regular users to only see their own documents
        """
        queryset = super().get_queryset()
        user = self.request.user
        
        # If not staff/admin, only show user's own documents
        if not user.is_staff:
            queryset = queryset.filter(benefit__member=user)
            
        return queryset
    
    def create(self, request, *args, **kwargs):
        """
        Create document and update the has_documentation flag on benefit
        """
        response = super().create(request, *args, **kwargs)
        
        # Update the has_documentation flag on the benefit
        if response.status_code == status.HTTP_201_CREATED:
            document = WelfareDocument.objects.get(id=response.data['id'])
            benefit = document.benefit
            if not benefit.has_documentation:
                benefit.has_documentation = True
                benefit.save()
        
        return response


class WelfareViewSet(viewsets.ModelViewSet):
    @action(detail=False, methods=['get'])
    def my_contributions(self, request):
        """Get current user's welfare contributions"""
        try:
            contributions = WelfareContribution.objects.filter(
                member=request.user
            ).select_related('welfare_fund').order_by('-contribution_date')

            # Check if can contribute this month
            current_month = timezone.now()
            has_contributed = contributions.filter(
                contribution_date__year=current_month.year,
                contribution_date__month=current_month.month,
                status='CONFIRMED'
            ).exists()

            data = {
                'contributions': WelfareContributionSerializer(contributions, many=True).data,
                'can_contribute': not has_contributed,
                'next_contribution_date': (current_month + timedelta(days=32)).replace(day=1) if has_contributed else None,
                'monthly_amount': 300  # Fixed amount
            }

            return Response(data)
        except Exception as e:
            logger.exception("Failed to fetch welfare contributions")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def initiate_payment(self, request):
        """Initiate welfare payment through M-Pesa"""
        try:
            phone_number = request.data.get('phone_number')
            amount = request.data.get('amount', 300)  # Default welfare amount

            if not phone_number:
                return Response({
                    'success': False,
                    'message': 'Phone number is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check if user can contribute this month
            latest_contribution = WelfareContribution.objects.filter(
                member=request.user,
                payment_date__month=timezone.now().month,
                payment_date__year=timezone.now().year
            ).first()

            if latest_contribution:
                return Response({
                    'success': False,
                    'message': 'Already contributed this month'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Initialize M-Pesa payment
            from mpesaconfig.views import trigger_stk_push
            response = trigger_stk_push(
                phone_number=phone_number,
                amount=amount,
                account_reference='WELFARE',
                transaction_desc='Monthly Welfare Contribution'
            )

            return Response(response)

        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)