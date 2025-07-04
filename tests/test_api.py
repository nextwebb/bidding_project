"""
Tests for the /api/bid/ REST endpoint
"""
import pytest
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from bidding.models import ProductBid


class TestBidEndpoint(APITestCase):
    """Test cases for the bid calculation REST API endpoint"""
    
    def setUp(self):
        """Set up test data"""
        self.url = reverse('bid_endpoint')
        
    def test_valid_bid_calculation(self):
        """Test successful bid calculation"""
        data = {
            'product_id': 123,
            'current_cpc': 1.0,
            'target_roas': 150.0
        }
        
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['adjusted_cpc'] == 1.5
        assert 'bid_id' in response.data
        
        # Verify data was saved to database
        bid = ProductBid.objects.get(id=response.data['bid_id'])
        assert bid.product_id == 123
        assert float(bid.current_cpc) == 1.0
        assert float(bid.target_roas) == 150.0
        assert float(bid.adjusted_cpc) == 1.5
        
    def test_invalid_product_id(self):
        """Test with invalid product ID"""
        data = {
            'product_id': '',
            'current_cpc': 1.0,
            'target_roas': 150.0
        }
        
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'errors' in response.data
        assert 'Invalid product ID' in response.data['errors']
        
    def test_invalid_current_cpc(self):
        """Test with invalid current CPC"""
        data = {
            'product_id': 123,
            'current_cpc': 'invalid',
            'target_roas': 150.0
        }
        
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'errors' in response.data
        assert 'Invalid current CPC' in response.data['errors']
        
    def test_invalid_target_roas(self):
        """Test with invalid target ROAS"""
        data = {
            'product_id': 123,
            'current_cpc': 1.0,
            'target_roas': 0.0
        }
        
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'errors' in response.data
        assert 'Invalid target ROAS' in response.data['errors']
        
    def test_missing_fields(self):
        """Test with missing required fields"""
        data = {
            'product_id': 123
        }
        
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'errors' in response.data
        
    def test_multiple_bids_same_product(self):
        """Test multiple bids for the same product"""
        data = {
            'product_id': 123,
            'current_cpc': 1.0,
            'target_roas': 150.0
        }
        
        # First bid
        response1 = self.client.post(self.url, data, format='json')
        assert response1.status_code == status.HTTP_200_OK
        
        # Second bid with different values
        data['current_cpc'] = 2.0
        data['target_roas'] = 200.0
        
        response2 = self.client.post(self.url, data, format='json')
        assert response2.status_code == status.HTTP_200_OK
        assert response2.data['adjusted_cpc'] == 4.0
        
        # Verify both bids are stored
        assert ProductBid.objects.filter(product_id=123).count() == 2

    def test_large_numbers(self):
        """Test with large CPC and ROAS values"""
        data = {
            'product_id': 123,
            'current_cpc': 999.99,
            'target_roas': 500.0
        }
        
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['adjusted_cpc'] == 4999.95

    def test_decimal_precision(self):
        """Test decimal precision handling"""
        data = {
            'product_id': 123,
            'current_cpc': 1.234,
            'target_roas': 123.456
        }
        
        response = self.client.post(self.url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        # Should round to 2 decimal places
        expected = round(1.234 * (123.456 / 100), 2)
        assert response.data['adjusted_cpc'] == expected
