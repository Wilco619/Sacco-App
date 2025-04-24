from django.contrib import admin
from .models import (
    FinancialPeriod, Member, Savings, Share, Dividend, MemberGroup,
    FeeType, Fee, MembershipFee, Profit
)

@admin.register(FinancialPeriod)
class FinancialPeriodAdmin(admin.ModelAdmin):
    list_display = ('period_name', 'start_date', 'end_date', 'status', 'closed_by', 'closed_at')
    list_filter = ('status',)
    search_fields = ('period_name',)


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'id_number', 'phone_number', 'email', 'status', 'registration_paid')
    list_filter = ('status', 'registration_paid', 'group')
    search_fields = ('full_name', 'id_number', 'email')


@admin.register(Savings)
class SavingsAdmin(admin.ModelAdmin):
    list_display = ('member', 'amount', 'date', 'type')
    list_filter = ('type',)
    search_fields = ('member__full_name',)


@admin.register(Share)
class ShareAdmin(admin.ModelAdmin):
    list_display = ('member', 'number_of_shares', 'unit_price', 'total_amount', 'purchase_date')
    search_fields = ('member__full_name',)


@admin.register(Dividend)
class DividendAdmin(admin.ModelAdmin):
    list_display = ('member', 'year', 'amount', 'payment_status', 'calculation_date', 'payment_date')
    list_filter = ('year', 'payment_status')
    search_fields = ('member__full_name',)


@admin.register(MemberGroup)
class MemberGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_date')
    search_fields = ('name',)


@admin.register(FeeType)
class FeeTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'calculation_method', 'rate_or_amount', 'application_frequency', 'active')
    list_filter = ('calculation_method', 'application_frequency', 'active')
    search_fields = ('name',)


@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):
    list_display = ('fee_type', 'member', 'amount', 'status', 'date_charged', 'date_paid', 'waived')
    list_filter = ('status', 'waived')
    search_fields = ('member__email', 'fee_type__name')


@admin.register(MembershipFee)
class MembershipFeeAdmin(admin.ModelAdmin):
    list_display = ('member', 'fee_type', 'amount', 'payment_date', 'mpesa_receipt', 'is_initial_payment')
    search_fields = ('member__full_name', 'mpesa_receipt')


@admin.register(Profit)
class ProfitAdmin(admin.ModelAdmin):
    list_display = ('amount', 'source', 'date_recorded', 'reference_id', 'member', 'financial_period')
    list_filter = ('source',)
    search_fields = ('reference_id', 'member__full_name')
