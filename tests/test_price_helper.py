"""
Tests for the PriceHelper class (PHP to Python port)
"""
import pytest
from bidding.price_helper import PriceHelper


class TestPriceHelper:
    """Test cases for the PriceHelper price calculation and validation"""
    
    def test_calculate_adjusted_cpc_basic(self):
        """Test basic CPC calculation"""
        result = PriceHelper.calculate_adjusted_cpc(1.0, 150.0)
        assert result == 1.5
        
    def test_calculate_adjusted_cpc_rounding(self):
        """Test proper rounding to 2 decimal places"""
        result = PriceHelper.calculate_adjusted_cpc(1.234, 123.0)
        assert result == 1.52
        
    def test_calculate_adjusted_cpc_zero_current_cpc(self):
        """Test calculation with zero current CPC"""
        result = PriceHelper.calculate_adjusted_cpc(0.0, 100.0)
        assert result == 0.0
        
    def test_calculate_adjusted_cpc_negative_current_cpc(self):
        """Test that negative current CPC raises ValueError"""
        with pytest.raises(ValueError, match='Current CPC must be non-negative'):
            PriceHelper.calculate_adjusted_cpc(-1.0, 100.0)
            
    def test_calculate_adjusted_cpc_zero_target_roas(self):
        """Test that zero target ROAS raises ValueError"""
        with pytest.raises(ValueError, match='Target ROAS must be greater than 0'):
            PriceHelper.calculate_adjusted_cpc(1.0, 0.0)
            
    def test_calculate_adjusted_cpc_negative_target_roas(self):
        """Test that negative target ROAS raises ValueError"""
        with pytest.raises(ValueError, match='Target ROAS must be greater than 0'):
            PriceHelper.calculate_adjusted_cpc(1.0, -50.0)
    
    def test_validate_bid_data_valid(self):
        """Test validation with valid data"""
        errors = PriceHelper.validate_bid_data('123', '1.50', '150.0')
        assert errors == []
        
    def test_validate_bid_data_invalid_product_id(self):
        """Test validation with invalid product ID"""
        errors = PriceHelper.validate_bid_data('', '1.50', '150.0')
        assert 'Invalid product ID' in errors
        
        errors = PriceHelper.validate_bid_data(None, '1.50', '150.0')
        assert 'Invalid product ID' in errors
        
        errors = PriceHelper.validate_bid_data('abc', '1.50', '150.0')
        assert 'Invalid product ID' in errors
    
    def test_validate_bid_data_invalid_current_cpc(self):
        """Test validation with invalid current CPC"""
        errors = PriceHelper.validate_bid_data('123', 'abc', '150.0')
        assert 'Invalid current CPC' in errors
        
        errors = PriceHelper.validate_bid_data('123', '-1.0', '150.0')
        assert 'Invalid current CPC' in errors
        
        errors = PriceHelper.validate_bid_data('123', None, '150.0')
        assert 'Invalid current CPC' in errors
    
    def test_validate_bid_data_invalid_target_roas(self):
        """Test validation with invalid target ROAS"""
        errors = PriceHelper.validate_bid_data('123', '1.50', 'abc')
        assert 'Invalid target ROAS' in errors
        
        errors = PriceHelper.validate_bid_data('123', '1.50', '0.0')
        assert 'Invalid target ROAS' in errors
        
        errors = PriceHelper.validate_bid_data('123', '1.50', '-50.0')
        assert 'Invalid target ROAS' in errors
        
        errors = PriceHelper.validate_bid_data('123', '1.50', None)
        assert 'Invalid target ROAS' in errors
    
    def test_validate_bid_data_multiple_errors(self):
        """Test validation with multiple invalid fields"""
        errors = PriceHelper.validate_bid_data('', 'abc', '0.0')
        assert len(errors) == 3
        assert 'Invalid product ID' in errors
        assert 'Invalid current CPC' in errors
        assert 'Invalid target ROAS' in errors
