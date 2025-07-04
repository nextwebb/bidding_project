#!/usr/bin/env python
"""
Script to test database performance before and after index optimization
"""
import os
import django
import pytest
from django.db import connection
from django.utils import timezone
from datetime import timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from bidding.models import ProductBid
from decimal import Decimal


def create_test_data():
    """Create test data for performance testing"""
    print("Creating test data...")
    
    # Clear existing data
    ProductBid.objects.all().delete()
    
    # Create test bids across different time periods
    base_time = timezone.now()
    
    for i in range(1000):
        ProductBid.objects.create(
            product_id=i % 100,  # 100 different products
            current_cpc=Decimal(f"{1.0 + (i % 10) * 0.1:.2f}"),
            target_roas=Decimal(f"{100 + (i % 50) * 5}"),
            adjusted_cpc=Decimal(f"{1.5 + (i % 10) * 0.15:.2f}"),
            calculated_at=base_time - timedelta(
                days=i % 14,  # Spread across 2 weeks
                hours=i % 24,
                minutes=i % 60
            )
        )
    
    print(f"Created {ProductBid.objects.count()} test records")


@pytest.mark.django_db
def test_query_performance():
    """Test the performance of the slow query"""
    print("\n" + "="*60)
    print("TESTING QUERY PERFORMANCE")
    print("="*60)
    
    # The problem query from the requirements
    query = """
    SELECT * FROM bidding_productbid 
    WHERE calculated_at > now() - interval '7 days' 
    ORDER BY product_id;
    """
    
    print("Query being tested:")
    print(query)
    print()
    
    # Get EXPLAIN ANALYZE results
    with connection.cursor() as cursor:
        explain_query = f"EXPLAIN ANALYZE {query}"
        cursor.execute(explain_query)
        results = cursor.fetchall()
        
        print("EXPLAIN ANALYZE Results:")
        print("-" * 40)
        for row in results:
            print(row[0])
    
    print()
    
    # Also test with Django ORM equivalent
    seven_days_ago = timezone.now() - timedelta(days=7)
    
    print("Django ORM equivalent:")
    print("ProductBid.objects.filter(calculated_at__gte=seven_days_ago).order_by('product_id')")
    
    # Execute and time the query
    import time
    start_time = time.time()
    
    queryset = ProductBid.objects.filter(
        calculated_at__gte=seven_days_ago
    ).order_by('product_id')
    
    # Force evaluation
    results = list(queryset)
    
    end_time = time.time()
    
    print(f"Returned {len(results)} records in {(end_time - start_time) * 1000:.2f}ms")


@pytest.mark.django_db
def show_indexes():
    """Show all indexes on the ProductBid table"""
    print("\n" + "="*60)
    print("CURRENT INDEXES ON bidding_productbid")
    print("="*60)
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                indexname,
                indexdef
            FROM pg_indexes 
            WHERE tablename = 'bidding_productbid'
            ORDER BY indexname;
        """)
        
        for row in cursor.fetchall():
            print(f"Index: {row[0]}")
            print(f"Definition: {row[1]}")
            print()


if __name__ == "__main__":
    print("Database Performance Test Script")
    print("="*60)
    
    # Show current indexes
    show_indexes()
    
    # Create test data if needed
    if ProductBid.objects.count() == 0:
        create_test_data()
    else:
        print(f"Using existing {ProductBid.objects.count()} records")
    
    # Test query performance
    test_query_performance()
    
    print("\nPerformance test completed!")
    print("\nTo see the impact of the index optimization:")
    print("1. Run this script before applying migration 0002")
    print("2. Apply migration: python manage.py migrate")
    print("3. Run this script again to see the improvement")
