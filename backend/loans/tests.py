from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from decimal import Decimal
from rest_framework.test import APITestCase
from rest_framework import status
from welfare.models import WelfareContribution, WelfareFund
from accounts.models import ShareCapital
from .models import Loan, Guarantor
from django.utils import timezone
from mpesaconfig.handlers.factory import PaymentHandlerFactory
from loans.models import LoanRepayment

User = get_user_model()

class LoanTests(APITestCase):
    def setUp(self):
        # Create groups
        self.member_group = Group.objects.create(name='Member')
        self.admin_group = Group.objects.create(name='Admin')

        # Create users
        self.member = User.objects.create_user(
            username='testmember',
            password='testpass123',
            id_number='12345678'
        )
        self.member.groups.add(self.member_group)

        self.admin = User.objects.create_user(
            username='testadmin',
            password='testpass123',
            id_number='87654321'
        )
        self.admin.groups.add(self.admin_group)

        # Create welfare fund
        self.welfare_fund = WelfareFund.objects.create(
            name='Test Fund',
            minimum_contribution=300
        )

        # Add welfare contribution
        WelfareContribution.objects.create(
            member=self.member,
            welfare_fund=self.welfare_fund,
            amount=300,
            status='CONFIRMED'
        )

        # Add shares
        ShareCapital.objects.create(
            member=self.member,
            total_value=Decimal('50000.00')
        )

    def test_loan_application_validation(self):
        self.client.force_authenticate(user=self.member)
        
        # Test loan application without required fields
        response = self.client.post('/api/loans/', {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test valid loan application
        response = self.client.post('/api/loans/', {
            'principal_amount': '20000.00',
            'repayment_period': 'MONTHLY',
            'purpose': 'Test loan'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_loan_approval_process(self):
        self.client.force_authenticate(user=self.admin)
        
        # Create a loan
        loan = Loan.objects.create(
            member=self.member,
            principal_amount=Decimal('20000.00'),
            status='PENDING'
        )

        # Test approval
        response = self.client.post(f'/api/loans/{loan.id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify loan status
        loan.refresh_from_db()
        self.assertEqual(loan.status, 'APPROVED')

    def test_guarantor_validation(self):
        self.client.force_authenticate(user=self.member)
        
        # Create another member as guarantor
        guarantor = User.objects.create_user(
            username='guarantor',
            password='testpass123',
            id_number='11223344'
        )
        guarantor.groups.add(self.member_group)
        
        # Add shares for guarantor
        ShareCapital.objects.create(
            member=guarantor,
            total_value=Decimal('30000.00')
        )

        # Create loan
        loan = Loan.objects.create(
            member=self.member,
            principal_amount=Decimal('20000.00'),
            status='PENDING'
        )

        # Test guarantor request
        response = self.client.post('/api/guarantors/', {
            'loan': loan.id,
            'guarantor': guarantor.id,
            'amount': '20000.00'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

class LoanPaymentTests(TestCase):
    def setUp(self):
        self.handler = PaymentHandlerFactory.get_handler('LOAN')

    def test_loan_payment_processing(self):
        # Create test loan
        loan = Loan.objects.create(
            principal_amount=Decimal('20000.00'),
            principal_balance=Decimal('20000.00'),
            status='ACTIVE'
        )

        # Create test payment
        payment = LoanRepayment.objects.create(
            loan=loan,
            amount=Decimal('2000.00'),
            payment_date=timezone.now(),
            status='PENDING'
        )

        # Process payment
        result = self.handler.process_payment(payment)
        self.assertTrue(result['success'])

        # Verify loan balance updated
        loan.refresh_from_db()
        self.assertEqual(loan.principal_balance, Decimal('18000.00'))
