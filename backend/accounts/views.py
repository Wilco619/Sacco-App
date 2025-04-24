from datetime import timezone
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
import logging
from .models import ShareCapital
from mpesaconfig.models import Transaction
from finance.models import Member, MemberGroup, MembershipFee, Savings, Share
from loans.models import Loan
from finance.services import MembershipService
from .serializers import (
    MemberSerializer, SavingsSerializer, LoanSerializer, 
    TransactionSerializer, ShareSerializer, DividendSerializer, 
    MemberGroupSerializer, ShareStatementSerializer
)

logger = logging.getLogger(__name__)

class MemberViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Member model - provides CRUD operations and additional actions
    """
    queryset = Member.objects.all()
    serializer_class = MemberSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'registration_date', 'group']
    search_fields = ['full_name', 'id_number', 'phone_number', 'email']
    ordering_fields = ['registration_date', 'full_name']
    
    @action(detail=True, methods=['get'])
    def savings(self, request, pk=None):
        """Get all savings for a specific member"""
        member = self.get_object()
        savings = Savings.objects.filter(member=member)
        serializer = SavingsSerializer(savings, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def loans(self, request, pk=None):
        """Get all loans for a specific member"""
        member = self.get_object()
        loans = Loan.objects.filter(member=member)
        serializer = LoanSerializer(loans, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        """Get all transactions for a specific member"""
        member = self.get_object()
        transactions = Transaction.objects.filter(member=member)
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def shares(self, request, pk=None):
        """Get all shares for a specific member"""
        member = self.get_object()
        shares = Share.objects.filter(member=member)
        serializer = ShareSerializer(shares, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def process_initial_payments(self, request, pk=None):
        """Process initial membership payments"""
        member = self.get_object()
        try:
            MembershipService.process_initial_payments(member, request.data)
            return Response({'status': 'success'})
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def process_monthly_share(self, request, pk=None):
        """Process monthly share payment"""
        member = self.get_object()
        try:
            MembershipService.process_monthly_share(
                member,
                request.data.get('amount'),
                request.data.get('receipt_number')
            )
            return Response({'status': 'success'})
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def process_monthly_welfare(self, request, pk=None):
        """Process monthly welfare fee"""
        member = self.get_object()
        try:
            MembershipService.process_monthly_welfare(
                member,
                request.data.get('receipt_number')
            )
            return Response({'status': 'success'})
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='registration-status')
    def registration_status(self, request):
        """Check member's registration payment status"""
        try:
            # Try to get member if exists
            member = Member.objects.filter(user=request.user).first()
            
            # If no member profile exists yet, return pending status
            if not member:
                logger.info(f"No member profile found for user ID: {request.user.id_number}")
                return Response({
                    'registration_paid': False,
                    'needs_payment': True,
                    'registration_fee': 1000.00,
                    'status': 'pending',
                    'has_profile': False,
                    'id_number': request.user.id_number
                })

            # If member exists, return their status
            return Response({
                'registration_paid': member.registration_paid,
                'needs_payment': not member.registration_paid,
                'registration_fee': 1000.00,
                'status': member.status,
                'has_profile': True,
                'id_number': member.id_number
            })

        except Exception as e:
            logger.error(f"Error checking registration status: {str(e)}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def registration_payment(self, request):
        """Process registration payment"""
        try:
            member = request.user.member
            if member.registration_paid:
                return Response({
                    'error': 'Registration already paid'
                }, status=status.HTTP_400_BAD_REQUEST)

            amount = Decimal(str(request.data.get('amount', 0)))
            receipt_number = request.data.get('receipt_number')

            if amount < 1000:
                return Response({
                    'error': 'Registration fee is 1000 KSH'
                }, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                # Create initial share entry
                Share.objects.create(
                    member=member,
                    number_of_shares=1,
                    unit_price=Decimal('1000.00'),
                    total_amount=Decimal('1000.00'),
                    receipt_number=receipt_number
                )

                # Update member status
                member.registration_paid = True
                member.status = 'active'
                member.total_shares = Decimal('1000.00')
                member.save()

                # Create membership fee record
                MembershipFee.objects.create(
                    member=member,
                    fee_type='membership',
                    amount=Decimal('1000.00'),
                    receipt_number=receipt_number,
                    is_initial_payment=True
                )

            return Response({
                'status': 'success',
                'message': 'Registration payment processed successfully'
            })

        except Member.DoesNotExist:
            return Response({
                'error': 'Member profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current member's profile"""
        try:
            member = Member.objects.get(user=request.user)
            return Response({
                'id_number': member.id_number,
                'phone_number': member.phone_number,
                'full_name': member.full_name,
                'email': member.email,
                'status': member.status
            })
        except Member.DoesNotExist:
            return Response({
                'error': 'Member profile not found'
            }, status=status.HTTP_404_NOT_FOUND)


class SavingsViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Savings model
    """
    queryset = Savings.objects.all()
    serializer_class = SavingsSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['member', 'date', 'type']
    ordering_fields = ['date', 'amount']
    
    @action(detail=False, methods=['get'])
    def total_by_member(self, request):
        """Get total savings by member"""
        from django.db.models import Sum
        
        totals = Savings.objects.values('member__full_name').annotate(
            total_savings=Sum('amount')
        ).order_by('-total_savings')
        
        return Response(totals)


class LoanViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Loan model
    """
    queryset = Loan.objects.all()
    serializer_class = LoanSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['member', 'status', 'loan_type', 'application_date']
    search_fields = ['purpose', 'member__full_name']
    ordering_fields = ['application_date', 'amount', 'interest_rate']
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        with transaction.atomic():
            loan = self.get_object()
            self.validate_loan_approval(loan)
            # Process approval
            # Create repayment schedule
            # Update member's credit status
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a loan application"""
        loan = self.get_object()
        if loan.status == 'pending':
            loan.status = 'rejected'
            loan.save()
            return Response({'status': 'loan rejected'})
        return Response({'status': 'cannot reject loan'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get all overdue loans"""
        from django.utils import timezone
        overdue_loans = Loan.objects.filter(
            status='approved',
            due_date__lt=timezone.now().date()
        )
        serializer = self.get_serializer(overdue_loans, many=True)
        return Response(serializer.data)


class ShareViewSet(viewsets.ModelViewSet):
    """ViewSet for Share model"""
    queryset = ShareCapital.objects.all()
    serializer_class = ShareSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def purchase_shares(self, request):
        """Handle monthly share purchase and compensation"""
        try:
            amount = Decimal(request.data.get('amount', 0))
            member = request.user
            
            with transaction.atomic():
                # Get or create member's share capital record
                share_capital, created = ShareCapital.objects.get_or_create(
                    member=member,
                    defaults={
                        'number_of_shares': 0,
                        'value_per_share': 1000,
                        'total_value': 0,
                        'monthly_contribution': 0,
                        'certificate_number': f"SH{member.id_number}{timezone.now().strftime('%Y%m')}"
                    }
                )

                # Calculate new monthly contribution
                new_monthly = amount if amount >= 1000 else 1000
                
                if not created and new_monthly > share_capital.monthly_contribution:
                    # Calculate compensation needed
                    compensation = share_capital.calculate_compensation_amount(new_monthly)
                    
                    if amount < (new_monthly + compensation):
                        return Response({
                            'error': 'Insufficient amount for compensation',
                            'required_amount': new_monthly + compensation,
                            'compensation_needed': compensation
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Apply compensation
                    share_capital.update_monthly_contribution(new_monthly, compensation)
                    
                    # Update number of shares including compensation
                    total_purchase = amount
                    new_shares = total_purchase // 1000
                    
                else:
                    # Regular monthly purchase
                    new_shares = amount // 1000
                
                # Update share capital
                share_capital.number_of_shares += new_shares
                share_capital.total_value = share_capital.number_of_shares * 1000
                share_capital.last_payment_date = timezone.now().date()
                share_capital.save()

                # Record transaction
                Transaction.objects.create(
                    transaction_id=f"SH{timezone.now().strftime('%Y%m%d%H%M%S')}",
                    member=member,
                    transaction_type='SHARE_PURCHASE',
                    amount=amount,
                    balance_after=share_capital.total_value,
                    description=f"Share purchase: {new_shares} shares at 1000 KSH each",
                    status='COMPLETED'
                )

                return Response({
                    'status': 'success',
                    'shares_purchased': new_shares,
                    'total_shares': share_capital.number_of_shares,
                    'total_value': share_capital.total_value,
                    'monthly_contribution': share_capital.monthly_contribution
                })

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def share_statement(self, request):
        """Get user's share statement"""
        try:
            # Changed from member to user to match MPesa transaction user field
            share_capital = ShareCapital.objects.filter(member=request.user).first()
            
            if not share_capital:
                return Response({
                    'total_value': 0,
                    'monthly_contribution': 0,
                    'last_payment_date': None,
                    'transactions': []
                })

            # Get share purchase transactions
            transactions = Transaction.objects.filter(
                user=request.user,
                payment_type='SHARES',
                status='COMPLETED'
            ).order_by('-timestamp')[:10]

            data = {
                'total_value': float(share_capital.total_value),  # Convert Decimal to float
                'monthly_contribution': float(share_capital.monthly_contribution),
                'last_payment_date': share_capital.last_payment_date,
                'number_of_shares': share_capital.number_of_shares,
                'value_per_share': float(share_capital.value_per_share),
                'transactions': [{
                    'date': t.timestamp,
                    'amount': float(t.amount),
                    'transaction_id': t.mpesa_code or t.checkout_request_id,
                    'status': t.status
                } for t in transactions]
            }

            return Response(data)
        except Exception as e:
            logger.error(f"Error fetching share statement: {str(e)}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def next_purchase_date(self, request):
        """Get the next available share purchase date"""
        try:
            share_capital = ShareCapital.objects.get(member=request.user)
            if share_capital.last_payment_date:
                next_date = share_capital.last_payment_date.replace(
                    day=1) + relativedelta(months=1)
                return Response({
                    'next_purchase_date': next_date,
                    'can_purchase_now': timezone.now().date().month != share_capital.last_payment_date.month
                })
            return Response({
                'next_purchase_date': None,
                'can_purchase_now': True
            })
        except ShareCapital.DoesNotExist:
            return Response({
                'next_purchase_date': None,
                'can_purchase_now': True
            })

    @action(detail=False, methods=['get'])
    def validate_amount(self, request):
        """Validate share purchase amount and calculate compensation if needed"""
        try:
            amount = Decimal(request.query_params.get('amount', 0))
            
            if amount % 1000 != 0:
                return Response({
                    'valid': False,
                    'error': 'Amount must be in multiples of 1000 KSH'
                }, status=status.HTTP_400_BAD_REQUEST)

            share_capital = ShareCapital.objects.filter(member=request.user).first()
            if not share_capital:
                return Response({
                    'valid': True,
                    'compensation_needed': 0,
                    'total_amount': amount
                })

            new_monthly = amount
            if new_monthly > share_capital.monthly_contribution:
                compensation = share_capital.calculate_compensation_amount(new_monthly)
                return Response({
                    'valid': True,
                    'compensation_needed': compensation,
                    'total_amount': amount + compensation,
                    'current_monthly': share_capital.monthly_contribution,
                    'new_monthly': new_monthly
                })

            return Response({
                'valid': True,
                'compensation_needed': 0,
                'total_amount': amount
            })

        except Exception as e:
            return Response({
                'valid': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def purchase_history(self, request):
        """Get member's share purchase history with pagination"""
        try:
            transactions = Transaction.objects.filter(
                member=request.user,
                transaction_type='SHARE_PURCHASE'
            ).order_by('-date')

            page = self.paginate_queryset(transactions)
            if page is not None:
                serializer = TransactionSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = TransactionSerializer(transactions, many=True)
            return Response(serializer.data)

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def process_mpesa_purchase(self, request):
        """Process M-Pesa share purchase"""
        try:
            checkout_request_id = request.data.get('checkout_request_id')
            amount = Decimal(request.data.get('amount', 0))

            with transaction.atomic():
                # Verify M-Pesa transaction
                mpesa_transaction = Transaction.objects.get(
                    checkout_request_id=checkout_request_id,
                    status='COMPLETED'
                )

                if mpesa_transaction.amount != amount:
                    raise ValueError('Transaction amount mismatch')

                # Process share purchase
                response = self.purchase_shares(request)
                
                # Update M-Pesa transaction
                mpesa_transaction.reference_number = response.data.get('transaction_id')
                mpesa_transaction.save()

                return Response(response.data)

        except Transaction.DoesNotExist:
            return Response({
                'error': 'Invalid or incomplete M-Pesa transaction'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def statement(self, request):
        """Get user's share statement"""
        try:
            share_capital = ShareCapital.objects.filter(member=request.user).first()
            
            if not share_capital:
                return Response({
                    'total_value': 0,
                    'monthly_contribution': 0,
                    'last_payment_date': None,
                    'transactions': []
                })

            # Get share purchase transactions
            transactions = Transaction.objects.filter(
                user=request.user,
                payment_type='SHARES',
                status='COMPLETED'
            ).order_by('-timestamp')[:10]

            data = {
                'total_value': share_capital.total_value,
                'monthly_contribution': share_capital.monthly_contribution,
                'last_payment_date': share_capital.last_payment_date,
                'number_of_shares': share_capital.number_of_shares,
                'value_per_share': share_capital.value_per_share,
                'transactions': [{
                    'date': t.timestamp,
                    'amount': t.amount,
                    'transaction_id': t.mpesa_code,
                    'status': t.status
                } for t in transactions]
            }

            return Response(data)
        except Exception as e:
            logger.error(f"Error fetching share statement: {str(e)}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def my_shares(self, request):
        """Get current user's shares information"""
        try:
            share_capital = ShareCapital.objects.filter(member=request.user).first()
            
            if not share_capital:
                return Response({
                    'number_of_shares': 0,
                    'value_per_share': 1000,
                    'total_value': 0,
                    'monthly_contribution': 0,
                    'last_payment_date': None,
                    'certificate_number': None,
                    'date_purchased': None,
                    'transactions': []
                })

            transactions = Transaction.objects.filter(
                user=request.user,
                payment_type='SHARES',
                status='COMPLETED'
            ).order_by('-timestamp')[:10]

            data = {
                'number_of_shares': share_capital.number_of_shares,
                'value_per_share': float(share_capital.value_per_share),
                'total_value': float(share_capital.total_value),
                'monthly_contribution': float(share_capital.monthly_contribution),
                'last_payment_date': share_capital.last_payment_date,
                'certificate_number': share_capital.certificate_number,
                'date_purchased': share_capital.date_purchased,
                'transactions': [{
                    'date': t.timestamp,
                    'amount': float(t.amount),
                    'transaction_id': t.mpesa_code or t.checkout_request_id,
                    'status': t.status,
                    'certificate_number': share_capital.certificate_number
                } for t in transactions]
            }

            return Response(data)
        except Exception as e:
            logger.error(f"Error fetching shares data: {str(e)}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'])
    def purchase(self, request):
        """Handle share purchase with M-Pesa payment"""
        try:
            amount = Decimal(request.data.get('amount', 0))
            member = request.user
            
            with transaction.atomic():
                share_capital, created = ShareCapital.objects.get_or_create(
                    member=member,
                    defaults={
                        'number_of_shares': 0,
                        'value_per_share': 1000,
                        'total_value': 0,
                        'monthly_contribution': 0,
                        'certificate_number': f"SH{member.id_number}{timezone.now().strftime('%Y%m')}"
                    }
                )

                # Calculate new shares
                new_shares = amount // 1000
                
                # Update share capital
                share_capital.number_of_shares += new_shares
                share_capital.total_value = share_capital.number_of_shares * 1000
                share_capital.last_payment_date = timezone.now().date()
                
                if amount > share_capital.monthly_contribution:
                    share_capital.monthly_contribution = amount
                
                share_capital.save()

                # Record transaction
                Transaction.objects.create(
                    user=member,
                    payment_type='SHARES',
                    amount=amount,
                    status='COMPLETED',
                    description=f"Share purchase: {new_shares} shares at 1000 KSH each"
                )

                return Response({
                    'success': True,
                    'shares_purchased': new_shares,
                    'total_shares': share_capital.number_of_shares,
                    'total_value': float(share_capital.total_value),
                    'monthly_contribution': float(share_capital.monthly_contribution)
                })

        except Exception as e:
            logger.error(f"Share purchase error: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def purchase_eligibility(self, request):
        """Check if user can purchase shares this month"""
        try:
            share_capital = ShareCapital.objects.filter(member=request.user).first()
            
            if not share_capital or not share_capital.last_payment_date:
                return Response({
                    'can_purchase': True,
                    'next_purchase_date': None,
                    'monthly_contribution': 0
                })

            current_date = timezone.now().date()
            last_payment_month = share_capital.last_payment_date.month
            current_month = current_date.month

            data = {
                'can_purchase': current_month != last_payment_month,
                'next_purchase_date': (
                    share_capital.last_payment_date.replace(day=1) + 
                    relativedelta(months=1)
                ) if current_month == last_payment_month else current_date,
                'monthly_contribution': float(share_capital.monthly_contribution)
            }

            return Response(data)

        except Exception as e:
            logger.error(f"Error checking purchase eligibility: {str(e)}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def validate_purchase(self, request):
        """Validate share purchase amount"""
        try:
            amount = Decimal(request.query_params.get('amount', 0))
            
            if amount % 1000 != 0:
                return Response({
                    'valid': False,
                    'error': 'Amount must be in multiples of 1000 KSH'
                }, status=status.HTTP_400_BAD_REQUEST)

            share_capital = ShareCapital.objects.filter(member=request.user).first()
            monthly_contribution = share_capital.monthly_contribution if share_capital else 0

            return Response({
                'valid': True,
                'shares': int(amount // 1000),
                'total_amount': float(amount),
                'current_monthly': float(monthly_contribution),
                'new_monthly': float(max(amount, monthly_contribution))
            })

        except Exception as e:
            return Response({
                'valid': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class MemberGroupViewSet(viewsets.ModelViewSet):
    """
    ViewSet for MemberGroup model
    """
    queryset = MemberGroup.objects.all()
    serializer_class = MemberGroupSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']
    
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """Get all members in a specific group"""
        group = self.get_object()
        members = Member.objects.filter(group=group)
        serializer = MemberSerializer(members, many=True)
        return Response(serializer.data)