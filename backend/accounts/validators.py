from rest_framework import serializers

class LoanValidator:
    @staticmethod
    def validate_loan_eligibility(member, amount):
        if member.savings < amount * 0.3:
            raise serializers.ValidationError(
                "Insufficient savings. Must have 30% of loan amount."
            )