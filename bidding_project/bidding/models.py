from django.db import models
from django.utils import timezone


class ProductBid(models.Model):
    product_id = models.IntegerField()
    current_cpc = models.DecimalField(max_digits=10, decimal_places=2)
    target_roas = models.DecimalField(max_digits=10, decimal_places=2)
    adjusted_cpc = models.DecimalField(max_digits=10, decimal_places=2)
    calculated_at = models.DateTimeField(default=timezone.now, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['calculated_at', 'product_id']),
        ]

    def __str__(self):
        return f"Bid for Product {self.product_id}: {self.adjusted_cpc}"
