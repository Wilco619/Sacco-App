from rest_framework import serializers
from django.utils import timezone
from .models import WelfareFund, WelfareContribution, WelfareBenefit, WelfareDocument
from users.models import CustomUser


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class WelfareFundSerializer(serializers.ModelSerializer):
    date_established = serializers.DateField(required=False)  # Make it optional
    
    class Meta:
        model = WelfareFund
        fields = [
            'id', 'name', 'description', 'total_amount',
            'date_established', 'contribution_frequency',
            'minimum_contribution', 'status'
        ]
    
    def validate_date_established(self, value):
        """
        Convert datetime to date if necessary
        """
        if hasattr(value, 'date'):
            return value.date()
        return value

    def create(self, validated_data):
        # Set default date if not provided
        if 'date_established' not in validated_data:
            validated_data['date_established'] = timezone.now().date()
        return super().create(validated_data)


class WelfareContributionSerializer(serializers.ModelSerializer):
    member = CustomUserSerializer(read_only=True)
    member_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        source='member',
        write_only=True
    )
    welfare_fund = WelfareFundSerializer(read_only=True)
    welfare_fund_id = serializers.PrimaryKeyRelatedField(
        queryset=WelfareFund.objects.all(),
        source='welfare_fund',
        write_only=True
    )
    processed_by = CustomUserSerializer(read_only=True)
    
    class Meta:
        model = WelfareContribution
        fields = [
            'id', 'member', 'member_id', 'welfare_fund', 'welfare_fund_id',
            'amount', 'contribution_date', 'payment_method', 'reference_number',
            'receipt_number', 'status', 'processed_by', 'processed_at'
        ]


class WelfareDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = WelfareDocument
        fields = [
            'id', 'benefit', 'document', 'title', 'description', 'uploaded_at'
        ]


class WelfareBenefitSerializer(serializers.ModelSerializer):
    member = CustomUserSerializer(read_only=True)
    member_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        source='member',
        write_only=True
    )
    welfare_fund = WelfareFundSerializer(read_only=True)
    welfare_fund_id = serializers.PrimaryKeyRelatedField(
        queryset=WelfareFund.objects.all(),
        source='welfare_fund',
        write_only=True
    )
    reviewed_by = CustomUserSerializer(read_only=True)
    approved_by = CustomUserSerializer(read_only=True)
    documents = WelfareDocumentSerializer(many=True, read_only=True)
    
    class Meta:
        model = WelfareBenefit
        fields = [
            'id', 'member', 'member_id', 'welfare_fund', 'welfare_fund_id',
            'reason', 'other_reason', 'amount', 'approved_amount', 'application_date',
            'approval_date', 'disbursement_date', 'status', 'has_documentation',
            'document_description', 'reviewed_by', 'approved_by', 'rejection_reason',
            'documents'
        ]


class WelfareDocumentDetailSerializer(serializers.ModelSerializer):
    benefit = WelfareBenefitSerializer(read_only=True)
    
    class Meta:
        model = WelfareDocument
        fields = [
            'id', 'benefit', 'document', 'title', 'description', 'uploaded_at'
        ]


class WelfarePaymentSerializer(serializers.ModelSerializer):
    member = CustomUserSerializer(read_only=True)
    
    class Meta:
        model = WelfareContribution
        fields = [
            'id', 'member', 'amount', 'contribution_date', 
            'payment_method', 'reference_number', 'status'
        ]