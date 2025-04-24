from django.contrib import admin
from django.utils.html import format_html
from .models import Transaction

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('mpesa_code', 'amount', 'phone_number', 'get_status', 'timestamp')
    list_filter = ('status', 'timestamp', 'result_code')
    search_fields = ('mpesa_code', 'phone_number', 'checkout_request_id')
    readonly_fields = ('timestamp', 'get_status_details')
    
    fieldsets = (
        ('Transaction Details', {
            'fields': (
                'mpesa_code', 
                'amount', 
                'phone_number',
                'checkout_request_id'
            )
        }),
        ('Status Information', {
            'fields': (
                'status',
                'result_code',
                'result_description',
                'get_status_details',
                'timestamp'
            )
        }),
    )

    def get_status(self, obj):
        status_colors = {
            'PENDING': 'orange',
            'COMPLETED': 'green',
            'CANCELLED': '#FF4444',
            'FAILED': 'red',
            'TIMEOUT': 'grey'
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            status_colors.get(obj.status, 'black'),
            obj.status
        )
    get_status.short_description = 'Status'

    def get_status_details(self, obj):
        if obj.result_code == '1032':
            return format_html(
                '<div style="color: #FF4444;">Transaction cancelled by user</div>'
                '<small>The user cancelled the STK push prompt on their phone</small>'
            )
        return obj.result_description or '-'
    get_status_details.short_description = 'Status Details'

    def has_delete_permission(self, request, obj=None):
        return False


