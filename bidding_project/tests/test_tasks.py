"""
Tests for async tasks
"""
import pytest
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch
from decimal import Decimal
from bidding.models import ProductBid
from bidding.tasks import daily_budget_audit


@pytest.mark.django_db
class TestDailyBudgetAudit(TestCase):
    """Test cases for the daily budget audit async task"""
    
    def setUp(self):
        """Set up test data"""
        # Create test bids with different scenarios
        now = timezone.now()
        
        # Bid within threshold (10% difference, threshold is 20%)
        ProductBid.objects.create(
            product_id=1,
            current_cpc=Decimal('1.00'),
            target_roas=Decimal('110.0'),
            adjusted_cpc=Decimal('1.10'),  # 10% increase
            calculated_at=now - timedelta(days=1)
        )
        
        # Bid exceeding threshold (30% difference, threshold is 20%)
        ProductBid.objects.create(
            product_id=2,
            current_cpc=Decimal('2.00'),
            target_roas=Decimal('165.0'),
            adjusted_cpc=Decimal('3.30'),  # 65% increase -> 1.30 difference > 0.40 threshold
            calculated_at=now - timedelta(days=2)
        )
        
        # Old bid (outside 7-day window)
        ProductBid.objects.create(
            product_id=3,
            current_cpc=Decimal('1.00'),
            target_roas=Decimal('200.0'),
            adjusted_cpc=Decimal('2.00'),  # 100% increase
            calculated_at=now - timedelta(days=8)
        )
        
        # Another flagged bid
        ProductBid.objects.create(
            product_id=4,
            current_cpc=Decimal('5.00'),
            target_roas=Decimal('140.0'),
            adjusted_cpc=Decimal('7.00'),  # 40% increase -> 2.00 difference > 1.00 threshold
            calculated_at=now - timedelta(days=3)
        )
    
    @patch('bidding.tasks.print')
    def test_daily_budget_audit_with_flagged_bids(self, mock_print):
        """Test audit task with some flagged bids"""
        result = daily_budget_audit()
        
        # Check return values
        assert result['total_bids'] == 3  # Only last 7 days
        assert result['flagged_bids'] == 2  # Products 2 and 4
        
        # Verify print statements were called
        mock_print.assert_called()
        
        # Check that the audit report was printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        report_content = ' '.join(print_calls)
        
        assert 'DAILY BUDGET AUDIT REPORT' in report_content
        assert 'Total Bids Reviewed: 3' in report_content
        assert 'Flagged Bids: 2' in report_content
        assert 'Product: 2' in report_content
        assert 'Product: 4' in report_content
    
    def test_daily_budget_audit_empty_database(self):
        """Test audit task with no bids in database"""
        ProductBid.objects.all().delete()
        
        with patch('bidding.tasks.print') as mock_print:
            result = daily_budget_audit()
            
            # Check return value
            assert result['total_bids'] == 0
            assert result['flagged_bids'] == 0
            
            # Check that appropriate message was printed
            mock_print.assert_called_with("Daily Budget Audit: No bids found in the last 7 days")
    
    @patch('bidding.tasks.print')
    def test_daily_budget_audit_no_flagged_bids(self, mock_print):
        """Test audit task when all bids are within threshold"""
        # Clear existing data and create only good bids
        ProductBid.objects.all().delete()
        
        now = timezone.now()
        ProductBid.objects.create(
            product_id=1,
            current_cpc=Decimal('1.00'),
            target_roas=Decimal('105.0'),
            adjusted_cpc=Decimal('1.05'),  # 5% increase, well within threshold
            calculated_at=now - timedelta(days=1)
        )
        
        result = daily_budget_audit()
        
        assert result['total_bids'] == 1
        assert result['flagged_bids'] == 0
        
        # Check that the "no flagged bids" message was printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        report_content = ' '.join(print_calls)
        assert 'No bids flagged' in report_content
    
    def test_threshold_calculation_edge_cases(self):
        """Test edge cases for threshold calculation"""
        ProductBid.objects.all().delete()
        
        now = timezone.now()
        
        # Bid exactly at threshold (20% difference)
        ProductBid.objects.create(
            product_id=1,
            current_cpc=Decimal('10.00'),
            target_roas=Decimal('120.0'),
            adjusted_cpc=Decimal('12.00'),  # Exactly 2.00 difference, threshold is 2.00
            calculated_at=now - timedelta(days=1)
        )
        
        with patch('bidding.tasks.print') as mock_print:
            result = daily_budget_audit()
            
            # Should not be flagged (difference equals threshold, not greater)
            assert result['flagged_bids'] == 0
        
        # Bid just over threshold
        ProductBid.objects.create(
            product_id=2,
            current_cpc=Decimal('10.00'),
            target_roas=Decimal('120.1'),
            adjusted_cpc=Decimal('12.01'),  # 2.01 difference > 2.00 threshold
            calculated_at=now - timedelta(days=1)
        )
        
        with patch('bidding.tasks.print') as mock_print:
            result = daily_budget_audit()
            
            # Should be flagged
            assert result['flagged_bids'] == 1
