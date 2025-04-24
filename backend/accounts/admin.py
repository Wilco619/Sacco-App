from django.contrib import admin
from .models import SavingsAccount, ShareCapital, AuditLog


@admin.register(SavingsAccount)
class SavingsAccountAdmin(admin.ModelAdmin):
    list_display = ('account_number', 'member', 'account_type', 'balance', 'status', 'date_opened')
    search_fields = ('account_number', 'member__email', 'member__first_name', 'member__last_name')
    list_filter = ('account_type', 'status', 'date_opened')
    readonly_fields = ('date_opened', 'last_interest_calculation')


@admin.register(ShareCapital)
class ShareCapitalAdmin(admin.ModelAdmin):
    list_display = ('certificate_number', 'member', 'number_of_shares', 'total_value', 'status', 'date_purchased')
    search_fields = ('certificate_number', 'member__email', 'member__first_name', 'member__last_name')
    list_filter = ('status', 'date_purchased')
    readonly_fields = ('date_purchased',)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'model_name', 'object_id', 'timestamp')
    search_fields = ('user__email', 'model_name', 'object_id', 'action')
    list_filter = ('model_name', 'action', 'timestamp')
    readonly_fields = ('user', 'action', 'model_name', 'object_id', 'changes', 'timestamp')
