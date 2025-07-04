# Generated migration for database performance optimization
# This addresses the slow query: SELECT * FROM bidding_productbid WHERE calculated_at > now() - interval '7 days' ORDER BY product_id

from django.db import migrations, models


class Migration(migrations.Migration):
    
    dependencies = [
        ('bidding', '0001_initial'),
    ]

    operations = [
        # Add an optimized index for the slow query
        # Since the query filters by calculated_at and orders by product_id,
        # we need a composite index with calculated_at first (for filtering)
        # and product_id second (for ordering)
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS bidding_productbid_performance_idx "
            "ON bidding_productbid (calculated_at DESC, product_id);",
            reverse_sql="DROP INDEX IF EXISTS bidding_productbid_performance_idx;"
        ),
    ]
