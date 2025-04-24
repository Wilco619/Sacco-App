from decimal import Decimal
from django.forms import ValidationError
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Sum, F, Q
from django.db import transaction
from django.contrib.auth.models import Group

from users.permissions import IsAdminUser, IsSelfOrAdmin

from loans.services import LoanProcessor

from .models import Loan, Guarantor, LoanRepayment, PenaltyType, Penalty
from .serializers import (
    LoanListSerializer, LoanDetailSerializer, GuarantorSerializer,
    LoanRepaymentSerializer, PenaltyTypeSerializer, PenaltySerializer
)


class LoanViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing loan operations
    """
    permission_classes = [IsAuthenticated]
    serializer_class = LoanDetailSerializer
    
    def get_queryset(self):
        if self.request.user.user_type == 'ADMIN':
            return Loan.objects.all().order_by('-application_date')
        return Loan.objects.filter(member=self.request.user).order_by('-application_date')

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['loan_type', 'status', 'member', 'has_collateral', 'term_months']
    search_fields = ['loan_id', 'member__first_name', 'member__last_name', 'purpose']
    ordering_fields = ['application_date', 'approval_date', 'disbursement_date', 'principal_amount']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return LoanListSerializer
        return LoanDetailSerializer
    
    def get_permissions(self):
        """
        Override to customize permissions based on action
        """
        if self.action in ['update', 'partial_update', 'destroy', 
                          'approve', 'reject', 'disburse', 'all']:
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]
    
    @action(detail=True, methods=['POST'])
    def approve(self, request, pk=None):
        loan = self.get_object()
        
        if loan.status != 'PENDING':
            return Response(
                {'error': 'Can only approve pending loans'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            LoanProcessor.process_loan_approval(loan, request.user)
            return Response({'message': 'Loan approval processed'})
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['GET'])
    def available_amount(self, request):
        """Get maximum loan amount available for member"""
        try:
            loan = Loan(member=request.user)
            amount_info = loan.get_available_loan_amount()
            return Response({
                'success': True,
                'data': amount_info
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request, *args, **kwargs):
        try:
            # Check available amount first
            loan = Loan(
                member=request.user,
                principal_amount=Decimal(request.data.get('principal_amount', 0))
            )
            amount_info = loan.get_available_loan_amount()
            
            if loan.principal_amount > amount_info['available_amount']:
                return Response({
                    'success': False,
                    'error': (
                        f"Loan amount exceeds available limit. "
                        f"Maximum amount available: KES {amount_info['available_amount']:,.2f} "
                        f"based on your shares value of KES {amount_info['shares_value']:,.2f}"
                    )
                }, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                # Add member to request data
                data = request.data.copy()
                data['member'] = request.user.id

                serializer = self.get_serializer(data=data)
                serializer.is_valid(raise_exception=True)
                
                # Save with member
                loan = serializer.save(member=request.user)

                return Response(
                    {
                        'success': True,
                        'message': 'Loan application submitted successfully',
                        'data': serializer.data
                    },
                    status=status.HTTP_201_CREATED
                )

        except ValidationError as e:
            return Response(
                {
                    'success': False,
                    'error': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {
                    'success': False,
                    'error': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a loan application"""
        loan = self.get_object()
        
        if loan.status not in ['APPLIED', 'UNDER_REVIEW']:
            return Response(
                {'error': f'Cannot reject loan in {loan.status} status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reason = request.data.get('rejection_reason')
        if not reason:
            return Response(
                {'error': 'Rejection reason is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        loan.status = 'REJECTED'
        loan.rejection_reason = reason
        loan.save()
        
        serializer = self.get_serializer(loan)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def send_to_review(self, request, pk=None):
        """Send a loan application for review"""
        loan = self.get_object()
        
        if loan.status != 'APPLIED':
            return Response(
                {'error': f'Cannot send to review a loan in {loan.status} status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        loan.status = 'UNDER_REVIEW'
        loan.save()
        
        serializer = self.get_serializer(loan)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def disburse(self, request, pk=None):
        """Disburse an approved loan"""
        loan = self.get_object()
        
        if loan.status != 'APPROVED':
            return Response(
                {'error': 'Only approved loans can be disbursed'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        first_payment_date = request.data.get('first_payment_date')
        if not first_payment_date:
            return Response(
                {'error': 'First payment date is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        loan.status = 'DISBURSED'
        loan.disbursement_date = timezone.now()
        loan.first_payment_date = first_payment_date
        loan.save()  # This will trigger the calculations in the save method
        
        serializer = self.get_serializer(loan)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def repayment_schedule(self, request, pk=None):
        """Generate a repayment schedule for the loan"""
        loan = self.get_object()
        
        if loan.status not in ['APPROVED', 'DISBURSED', 'ACTIVE']:
            return Response(
                {'error': 'Cannot generate schedule for non-approved/disbursed loan'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate the repayment schedule based on loan parameters
        schedule = []
        
        if loan.first_payment_date:
            total_principal = float(loan.principal_amount)
            total_interest = float(loan.total_interest)
            
            monthly_principal = total_principal / loan.term_months
            
            if loan.interest_type == 'FLAT':
                monthly_interest = total_interest / loan.term_months
            
            payment_date = loan.first_payment_date
            
            remaining_principal = total_principal
            remaining_interest = total_interest
            
            for month in range(1, loan.term_months + 1):
                if loan.interest_type == 'REDUCING' and month > 1:
                    # Recalculate interest for reducing balance
                    monthly_interest = (remaining_principal * float(loan.interest_rate)) / (100 * 12)
                
                # Adjust the final payment to account for rounding errors
                if month == loan.term_months:
                    principal_payment = remaining_principal
                    interest_payment = remaining_interest
                else:
                    principal_payment = monthly_principal
                    interest_payment = monthly_interest if loan.interest_type == 'FLAT' else monthly_interest
                
                total_payment = principal_payment + interest_payment
                
                remaining_principal -= principal_payment
                remaining_interest -= interest_payment
                
                schedule.append({
                    'installment_number': month,
                    'due_date': payment_date.strftime('%Y-%m-%d'),
                    'principal_component': round(principal_payment, 2),
                    'interest_component': round(interest_payment, 2),
                    'total_payment': round(total_payment, 2),
                    'principal_balance': round(max(0, remaining_principal), 2),
                    'interest_balance': round(max(0, remaining_interest), 2)
                })
                
                # Calculate next payment date based on frequency
                if loan.repayment_frequency == 'MONTHLY':
                    # Add a month
                    month_value = payment_date.month + 1
                    year_value = payment_date.year + month_value // 13
                    month_value = (month_value % 12) or 12  # Convert 0 to 12
                    payment_date = payment_date.replace(year=year_value, month=month_value)
                elif loan.repayment_frequency == 'WEEKLY':
                    payment_date += timezone.timedelta(days=7)
                elif loan.repayment_frequency == 'DAILY':
                    payment_date += timezone.timedelta(days=1)
                elif loan.repayment_frequency == 'QUARTERLY':
                    # Add three months
                    month_value = payment_date.month + 3
                    year_value = payment_date.year + month_value // 13
                    month_value = (month_value % 12) or 12
                    payment_date = payment_date.replace(year=year_value, month=month_value)
        
        return Response(schedule)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get loan statistics"""
        # Total active loans and values
        active_loans = Loan.objects.filter(status__in=['DISBURSED', 'ACTIVE'])
        active_count = active_loans.count()
        active_principal = active_loans.aggregate(total=Sum('principal_amount'))['total'] or 0
        active_balance = active_loans.aggregate(total=Sum('principal_balance'))['total'] or 0
        
        # Loans by type
        loans_by_type = {}
        for loan_type, _ in Loan.LOAN_TYPE_CHOICES:
            count = Loan.objects.filter(loan_type=loan_type).count()
            amount = Loan.objects.filter(loan_type=loan_type).aggregate(
                total=Sum('principal_amount'))['total'] or 0
            loans_by_type[loan_type] = {'count': count, 'amount': amount}
        
        # Loans by status
        loans_by_status = {}
        for status, _ in Loan.STATUS_CHOICES:
            count = Loan.objects.filter(status=status).count()
            amount = Loan.objects.filter(status=status).aggregate(
                total=Sum('principal_amount'))['total'] or 0
            loans_by_status[status] = {'count': count, 'amount': amount}
        
        # Defaulted loans
        defaulted_count = Loan.objects.filter(status='DEFAULTED').count()
        defaulted_amount = Loan.objects.filter(status='DEFAULTED').aggregate(
            total=Sum('principal_balance'))['total'] or 0
        
        # Calculate default rate
        total_completed = Loan.objects.filter(
            status__in=['FULLY_PAID', 'DEFAULTED', 'WRITTEN_OFF']).count()
        default_rate = (defaulted_count / total_completed) * 100 if total_completed > 0 else 0
        
        return Response({
            'active_loans': {
                'count': active_count,
                'principal_value': active_principal,
                'outstanding_balance': active_balance
            },
            'loans_by_type': loans_by_type,
            'loans_by_status': loans_by_status,
            'default_metrics': {
                'defaulted_count': defaulted_count,
                'defaulted_amount': defaulted_amount,
                'default_rate': default_rate
            }
        })

    @action(detail=False, methods=['GET'])
    def loan_eligibility(self, request):
        """Get member's loan eligibility status including welfare and shares"""
        try:
            from welfare.models import WelfareContribution
            from accounts.models import ShareCapital
            from django.utils import timezone

            # Get current month welfare status
            current_month = timezone.now()
            welfare_status = WelfareContribution.objects.filter(
                member=request.user,
                contribution_date__year=current_month.year,
                contribution_date__month=current_month.month,
                status='CONFIRMED'
            ).exists()

            # Get shares and loan amount info
            loan = Loan(member=request.user)
            amount_info = loan.get_available_loan_amount()

            # Check active loans
            has_active_loan = Loan.objects.filter(
                member=request.user,
                status__in=['APPROVED', 'DISBURSED', 'ACTIVE']
            ).exists()

            return Response({
                'success': True,
                'data': {
                    'welfare_paid': welfare_status,
                    'available_amount': amount_info['available_amount'],
                    'shares_value': amount_info['shares_value'],
                    'has_active_loan': has_active_loan,
                    'can_apply': welfare_status and not has_active_loan
                }
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['GET'])
    def all(self, request):
        """Get all loans - admin only endpoint"""
        try:
            loans = self.get_queryset()
            serializer = self.get_serializer(loans, many=True)
            
            return Response({
                'success': True,
                'data': serializer.data
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GuarantorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing loan guarantors
    """
    queryset = Guarantor.objects.all()
    serializer_class = GuarantorSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['loan', 'guarantor', 'status']
    ordering_fields = ['request_date', 'response_date']
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Accept a guarantor request"""
        guarantor = self.get_object()
        
        if guarantor.status != 'REQUESTED':
            return Response(
                {'error': 'Only pending guarantor requests can be accepted'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Ensure the logged-in user is the guarantor
        if request.user.id != guarantor.guarantor.id:
            return Response(
                {'error': 'Only the guarantor can accept this request'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        guarantor.status = 'ACCEPTED'
        guarantor.response_date = timezone.now()
        guarantor.save()
        
        serializer = self.get_serializer(guarantor)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a guarantor request"""
        guarantor = self.get_object()
        
        if guarantor.status != 'REQUESTED':
            return Response(
                {'error': 'Only pending guarantor requests can be rejected'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Ensure the logged-in user is the guarantor
        if request.user.id != guarantor.guarantor.id:
            return Response(
                {'error': 'Only the guarantor can reject this request'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        rejection_reason = request.data.get('rejection_reason')
        if not rejection_reason:
            return Response(
                {'error': 'Rejection reason is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        guarantor.status = 'REJECTED'
        guarantor.response_date = timezone.now()
        guarantor.rejection_reason = rejection_reason
        guarantor.save()
        
        serializer = self.get_serializer(guarantor)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_guarantees(self, request):
        """Get guarantees where the current user is a guarantor"""
        guarantees = Guarantor.objects.filter(guarantor=request.user)
        serializer = self.get_serializer(guarantees, many=True)
        return Response(serializer.data)


class LoanRepaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing loan repayments
    """
    queryset = LoanRepayment.objects.all()
    serializer_class = LoanRepaymentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['loan', 'status', 'payment_method']
    ordering_fields = ['payment_date']
    
    @action(detail=True, methods=['post'])
    def process_payment(self, request, pk=None):
        """Process a pending payment"""
        repayment = self.get_object()
        
        if repayment.status != 'PENDING':
            return Response(
                {'error': 'Only pending payments can be processed'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                loan = repayment.loan
                
                # Update loan balances
                loan.principal_balance -= repayment.principal_component
                loan.interest_balance -= repayment.interest_component
                
                # Check if loan is fully paid
                if loan.principal_balance <= 0 and loan.interest_balance <= 0:
                    loan.status = 'FULLY_PAID'
                elif loan.status == 'DISBURSED':
                    loan.status = 'ACTIVE'
                
                loan.save()
                
                # Update repayment status
                repayment.status = 'PROCESSED'
                repayment.processed_by = request.user
                repayment.principal_balance_after = loan.principal_balance
                repayment.interest_balance_after = loan.interest_balance
                repayment.save()
                
                serializer = self.get_serializer(repayment)
                return Response(serializer.data)
        
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def payment_history(self, request):
        """Get payment history for a specific loan"""
        loan_id = request.query_params.get('loan')
        if not loan_id:
            return Response(
                {'error': 'Loan ID is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        repayments = LoanRepayment.objects.filter(loan=loan_id).order_by('-payment_date')
        serializer = self.get_serializer(repayments, many=True)
        return Response(serializer.data)


class PenaltyTypeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing penalty types
    """
    queryset = PenaltyType.objects.all()
    serializer_class = PenaltyTypeSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get only active penalty types"""
        active_types = PenaltyType.objects.filter(active=True)
        serializer = self.get_serializer(active_types, many=True)
        return Response(serializer.data)


class PenaltyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing penalties
    """
    queryset = Penalty.objects.all()
    serializer_class = PenaltySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['loan', 'penalty_type', 'status', 'waived']
    ordering_fields = ['date_imposed', 'due_date']
    
    @action(detail=True, methods=['post'])
    def waive(self, request, pk=None):
        """Waive a penalty"""
        penalty = self.get_object()
        
        if penalty.status == 'PAID':
            return Response(
                {'error': 'Cannot waive a paid penalty'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        waiver_reason = request.data.get('waiver_reason')
        if not waiver_reason:
            return Response(
                {'error': 'Waiver reason is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        penalty.status = 'WAIVED'
        penalty.waived = True
        penalty.waiver_reason = waiver_reason
        penalty.waived_by = request.user
        penalty.waived_at = timezone.now()
        penalty.save()
        
        serializer = self.get_serializer(penalty)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def calculate_late_penalties(self, request):
        """Calculate penalties for late payments"""
        try:
            # Find active loans with due payments
            current_date = timezone.now().date()
            
            # Get all available penalty types
            penalty_types = PenaltyType.objects.filter(active=True)
            if not penalty_types.exists():
                return Response(
                    {'error': 'No active penalty types found'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Default to the first penalty type
            late_payment_penalty = penalty_types.first()
            
            # Get active loans
            active_loans = Loan.objects.filter(
                status__in=['DISBURSED', 'ACTIVE']
            )
            
            penalties_created = 0
            
            for loan in active_loans:
                # Very simplified approach - in a real system, would need to track
                # scheduled payments and check against actual payments
                
                # For this example, we'll just check if any payment was made in the last month
                last_payment = LoanRepayment.objects.filter(
                    loan=loan,
                    status='PROCESSED',
                    payment_date__gte=timezone.now() - timezone.timedelta(days=30)
                ).exists()
                
                # If no payment in last month and loan has been active for at least a month
                if not last_payment and loan.disbursement_date and \
                   loan.disbursement_date < timezone.now() - timezone.timedelta(days=30):
                    
                    # Check if a penalty already exists for this period
                    existing_penalty = Penalty.objects.filter(
                        loan=loan,
                        date_imposed__gte=timezone.now() - timezone.timedelta(days=30)
                    ).exists()
                    
                    if not existing_penalty:
                        # Calculate penalty amount
                        if late_payment_penalty.calculation_method == 'FIXED':
                            penalty_amount = late_payment_penalty.rate_or_amount
                        else:  # PERCENTAGE
                            # Calculate as percentage of outstanding balance
                            penalty_amount = (loan.principal_balance * late_payment_penalty.rate_or_amount) / 100
                        
                        # Create the penalty
                        Penalty.objects.create(
                            loan=loan,
                            penalty_type=late_payment_penalty,
                            amount=penalty_amount,
                            due_date=current_date + timezone.timedelta(days=15),  # Due in 15 days
                            status='IMPOSED'
                        )
                        penalties_created += 1
            
            return Response({
                'message': f'Successfully created {penalties_created} penalties',
                'penalties_created': penalties_created
            })
        
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )