from django.contrib import admin
from .models import ProductBid


@admin.register(ProductBid)
class ProductBidAdmin(admin.ModelAdmin):
    list_display = ('product_id', 'current_cpc', 'adjusted_cpc', 'target_roas', 'calculated_at')
    list_filter = ('calculated_at', 'product_id')
    search_fields = ('product_id',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-calculated_at',)
