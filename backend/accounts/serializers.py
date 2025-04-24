from rest_framework import serializers

from mpesaconfig.serializers import TransactionSerializer
from finance.models import Dividend, Member, MemberGroup, Savings, Share
from loans.models import Loan
from .models import ShareCapital

class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = '__all__'


class SavingsSerializer(serializers.ModelSerializer):
    member_name = serializers.ReadOnlyField(source='member.full_name')
    
    class Meta:
        model = Savings
        fields = '__all__'


class LoanSerializer(serializers.ModelSerializer):
    member_name = serializers.ReadOnlyField(source='member.full_name')
    
    class Meta:
        model = Loan
        fields = '__all__'


class ShareSerializer(serializers.ModelSerializer):
    member_name = serializers.ReadOnlyField(source='member.full_name')
    
    class Meta:
        model = Share
        fields = '__all__'


class DividendSerializer(serializers.ModelSerializer):
    member_name = serializers.ReadOnlyField(source='member.full_name')
    
    class Meta:
        model = Dividend
        fields = '__all__'


class MemberGroupSerializer(serializers.ModelSerializer):
    members = MemberSerializer(many=True, read_only=True)
    
    class Meta:
        model = MemberGroup
        fields = '__all__'


class ShareStatementSerializer(serializers.ModelSerializer):
    transactions = TransactionSerializer(many=True, read_only=True)

    class Meta:
        model = ShareCapital
        fields = [
            'total_value',
            'monthly_contribution',
            'last_payment_date',
            'transactions'
        ]