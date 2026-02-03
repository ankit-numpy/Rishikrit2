from django.contrib import admin
from .models import Coupon, DeliveryRate, Order, OrderItem, Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'inventory', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'value', 'min_order_amount', 'active', 'used_count')
    list_filter = ('active', 'discount_type')
    search_fields = ('code',)

@admin.register(DeliveryRate)
class DeliveryRateAdmin(admin.ModelAdmin):
    list_display = ('name', 'fee', 'free_over', 'is_active')
    list_filter = ('is_active',)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'price', 'quantity')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'phone', 'status', 'payment_method', 'payment_status', 'created_at')
    list_editable = ('status', 'payment_status')
    list_filter = ('status', 'payment_method', 'payment_status', 'created_at')
    search_fields = ('full_name', 'phone')
    inlines = [OrderItemInline]
    fields = (
        'full_name',
        'phone',
        'email',
        'address',
        'city',
        'state',
        'postal_code',
        'notes',
        'status',
        'payment_method',
        'payment_status',
        'payment_reference',
        'coupon',
        'discount_amount',
        'delivery_fee',
    )
