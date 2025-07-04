"""
Integration tests for the complete bidding system
"""
import pytest
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch
from bidding.models import ProductBid
from bidding.tasks import daily_budget_audit


@pytest.mark.django_db
class BiddingSystemIntegrationTest(TestCase):
    """Full integration test of the bidding system"""
    
    def setUp(self):
        self.client = APIClient()
        
    def test_complete_bidding_workflow(self):
        """Test the complete workflow: API call → DB storage → Audit"""
        
        # Step 1: Create multiple bids via API
        bid_data = [
            {'product_id': 1, 'current_cpc': 1.0, 'target_roas': 110.0},  # Small adjustment
            {'product_id': 2, 'current_cpc': 2.0, 'target_roas': 165.0},  # Large adjustment (flagged)
            {'product_id': 3, 'current_cpc': 5.0, 'target_roas': 140.0},  # Large adjustment (flagged)
        ]
        
        bid_ids = []
        for data in bid_data:
            response = self.client.post('/api/bid/', data, format='json')
            assert response.status_code == status.HTTP_200_OK
            bid_ids.append(response.data['bid_id'])
        
        # Step 2: Verify bids are stored correctly
        assert ProductBid.objects.count() == 3
        
        bid1 = ProductBid.objects.get(id=bid_ids[0])
        assert bid1.product_id == 1
        assert float(bid1.adjusted_cpc) == 1.1  # 1.0 * (110/100)
        
        bid2 = ProductBid.objects.get(id=bid_ids[1])
        assert bid2.product_id == 2
        assert float(bid2.adjusted_cpc) == 3.3  # 2.0 * (165/100)
        
        bid3 = ProductBid.objects.get(id=bid_ids[2])
        assert bid3.product_id == 3
        assert float(bid3.adjusted_cpc) == 7.0  # 5.0 * (140/100)
        
        # Step 3: Run the audit task
        with patch('bidding.tasks.print') as mock_print:
            result = daily_budget_audit()
        
        # Step 4: Verify audit results
        assert result['total_bids'] == 3
        assert result['flagged_bids'] == 2  # Products 2 and 3 should be flagged
        
        # Verify the audit identified the correct flagged bids
        # Bid 1: diff = |1.1 - 1.0| = 0.1, threshold = 0.2 * 1.0 = 0.2 → NOT flagged
        # Bid 2: diff = |3.3 - 2.0| = 1.3, threshold = 0.2 * 2.0 = 0.4 → FLAGGED 
        # Bid 3: diff = |7.0 - 5.0| = 2.0, threshold = 0.2 * 5.0 = 1.0 → FLAGGED
        
        # Check that audit report was printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        report_content = ' '.join(print_calls)
        
        assert 'DAILY BUDGET AUDIT REPORT' in report_content
        assert 'Total Bids Reviewed: 3' in report_content
        assert 'Flagged Bids: 2' in report_content
        assert 'Product: 2' in report_content
        assert 'Product: 3' in report_content
        assert 'Product: 1' not in report_content.split('FLAGGED BIDS')[1] if 'FLAGGED BIDS' in report_content else True

    def test_edge_case_threshold_calculations(self):
        """Test edge cases for the audit threshold calculations"""
        
        # Create a bid exactly at the threshold
        response = self.client.post('/api/bid/', {
            'product_id': 100,
            'current_cpc': 10.0,
            'target_roas': 120.0  # Results in 12.0 adjusted CPC, diff = 2.0, threshold = 2.0
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['adjusted_cpc'] == 12.0
        
        # Run audit - should NOT be flagged (diff equals threshold, not greater)
        with patch('bidding.tasks.print'):
            result = daily_budget_audit()
            
        assert result['flagged_bids'] == 0
        
        # Create a bid just over the threshold
        response = self.client.post('/api/bid/', {
            'product_id': 101,
            'current_cpc': 10.0,
            'target_roas': 120.1  # Results in 12.01 adjusted CPC, diff = 2.01, threshold = 2.0
        }, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['adjusted_cpc'] == 12.01
        
        # Run audit - should be flagged
        with patch('bidding.tasks.print'):
            result = daily_budget_audit()
            
        assert result['flagged_bids'] == 1

    def test_historical_data_filtering(self):
        """Test that audit only considers last 7 days of data"""
        
        now = timezone.now()
        
        # Create old bid (outside 7-day window)
        old_bid = ProductBid.objects.create(
            product_id=200,
            current_cpc=Decimal('1.0'),
            target_roas=Decimal('300.0'),  # Would be flagged if considered
            adjusted_cpc=Decimal('3.0'),
            calculated_at=now - timedelta(days=8)
        )
        
        # Create recent bid (within 7-day window)
        recent_response = self.client.post('/api/bid/', {
            'product_id': 201,
            'current_cpc': 1.0,
            'target_roas': 105.0  # Small adjustment, won't be flagged
        }, format='json')
        
        assert recent_response.status_code == status.HTTP_200_OK
        
        # Run audit
        with patch('bidding.tasks.print'):
            result = daily_budget_audit()
        
        # Only recent bid should be considered
        assert result['total_bids'] == 1
        assert result['flagged_bids'] == 0

    def test_error_handling_and_validation(self):
        """Test API error handling"""
        
        # Test invalid data
        invalid_requests = [
            {'product_id': '', 'current_cpc': 1.0, 'target_roas': 100.0},
            {'product_id': 123, 'current_cpc': 'abc', 'target_roas': 100.0},
            {'product_id': 123, 'current_cpc': 1.0, 'target_roas': 0.0},
            {'product_id': 123, 'current_cpc': -1.0, 'target_roas': 100.0},
            {},  # Missing all fields
        ]
        
        for invalid_data in invalid_requests:
            response = self.client.post('/api/bid/', invalid_data, format='json')
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert 'error' in response.data or 'errors' in response.data
        
        # Verify no invalid bids were stored
        assert ProductBid.objects.count() == 0
