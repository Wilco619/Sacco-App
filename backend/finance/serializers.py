from rest_framework import serializers
from .models import FinancialPeriod, Dividend, FeeType, Fee
from users.models import CustomUser


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class FinancialPeriodSerializer(serializers.ModelSerializer):
    closed_by = CustomUserSerializer(read_only=True)
    
    class Meta:
        model = FinancialPeriod
        fields = [
            'id', 'period_name', 'start_date', 'end_date', 'status',
            'description', 'closed_by', 'closed_at'
        ]


class DividendSerializer(serializers.ModelSerializer):
    financial_period = FinancialPeriodSerializer(read_only=True)
    financial_period_id = serializers.PrimaryKeyRelatedField(
        queryset=FinancialPeriod.objects.all(),
        source='financial_period',
        write_only=True
    )
    approved_by = CustomUserSerializer(read_only=True)
    
    class Meta:
        model = Dividend
        fields = [
            'id', 'financial_period', 'financial_period_id', 'declaration_date', 
            'approval_date', 'payment_date', 'total_amount', 'dividend_rate',
            'status', 'description', 'approved_by'
        ]
        

class MemberDividendSerializer(serializers.ModelSerializer):
    dividend = DividendSerializer(read_only=True)
    dividend_id = serializers.PrimaryKeyRelatedField(
        queryset=Dividend.objects.all(),
        source='dividend',
        write_only=True
    )
    member = CustomUserSerializer(read_only=True)
    member_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        source='member',
        write_only=True
    )
    processed_by = CustomUserSerializer(read_only=True)
    
    class Meta:
        model = Dividend
        fields = [
            'id', 'dividend', 'dividend_id', 'member', 'member_id', 'share_count',
            'amount', 'payment_method', 'payment_reference', 'payment_status',
            'processed_date', 'processed_by'
        ]


class FeeTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeeType
        fields = [
            'id', 'name', 'description', 'calculation_method', 'rate_or_amount',
            'minimum_amount', 'maximum_amount', 'application_frequency', 'active'
        ]


class FeeSerializer(serializers.ModelSerializer):
    fee_type = FeeTypeSerializer(read_only=True)
    fee_type_id = serializers.PrimaryKeyRelatedField(
        queryset=FeeType.objects.all(),
        source='fee_type',
        write_only=True
    )
    member = CustomUserSerializer(read_only=True)
    member_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        source='member',
        write_only=True
    )
    waived_by = CustomUserSerializer(read_only=True)
    
    class Meta:
        model = Fee
        fields = [
            'id', 'fee_type', 'fee_type_id', 'member', 'member_id', 'amount',
            'date_charged', 'due_date', 'description', 'status', 'date_paid',
            'waived', 'waiver_reason', 'waived_by'
        ]