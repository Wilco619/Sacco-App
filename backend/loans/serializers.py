from datetime import timezone
from rest_framework import serializers
from django.utils import timezone
from .models import Loan, Guarantor, LoanRepayment, PenaltyType, Penalty
from users.models import CustomUser

# User serializer for reference fields
class UserReferenceSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name')
    
    class Meta:
        model = CustomUser
        fields = ['id', 'full_name', 'email', 'username']


class GuarantorSerializer(serializers.ModelSerializer):
    guarantor_name = serializers.CharField(source='guarantor.get_full_name', read_only=True)
    guarantor_details = UserReferenceSerializer(source='guarantor', read_only=True)
    
    class Meta:
        model = Guarantor
        fields = '__all__'


class LoanRepaymentSerializer(serializers.ModelSerializer):
    processed_by_name = serializers.CharField(source='processed_by.get_full_name', read_only=True)
    
    class Meta:
        model = LoanRepayment
        fields = '__all__'


class PenaltyTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PenaltyType
        fields = '__all__'


class PenaltySerializer(serializers.ModelSerializer):
    penalty_type_name = serializers.CharField(source='penalty_type.name', read_only=True)
    waived_by_name = serializers.CharField(source='waived_by.get_full_name', read_only=True)
    
    class Meta:
        model = Penalty
        fields = '__all__'


class LoanListSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.get_full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    
    class Meta:
        model = Loan
        fields = '__all__'


class LoanDetailSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.get_full_name', read_only=True)
    application_date = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Loan
        fields = [
            'id', 'loan_id', 'member', 'member_name',
            'principal_amount', 'interest_rate',
            'repayment_period', 'purpose', 'status',
            'term_months', 'loan_type', 'application_date',
            'due_date', 'pending_approvals'
        ]
        read_only_fields = [
            'loan_id', 'member', 'member_name',
            'application_date', 'pending_approvals'
        ]

    def create(self, validated_data):
        validated_data['application_date'] = timezone.now()
        loan = super().create(validated_data)
        loan.loan_id = f"L{timezone.now().strftime('%Y%m%d')}{loan.id:04d}"
        loan.save()
        return loan