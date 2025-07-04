"""
Python port of legacy/priceHelper.php
Maintains identical behavior and validation logic
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Union


class PriceHelper:
    @staticmethod
    def calculate_adjusted_cpc(current_cpc: Union[float, Decimal], target_roas: Union[float, Decimal]) -> float:
        """
        Calculate adjusted CPC based on current CPC and target ROAS.
        
        Args:
            current_cpc: Current cost per click
            target_roas: Target return on ad spend
            
        Returns:
            Adjusted CPC rounded to 2 decimal places
            
        Raises:
            ValueError: If target ROAS <= 0 or current CPC < 0
        """
        if target_roas <= 0:
            raise ValueError('Target ROAS must be greater than 0')
        
        if current_cpc < 0:
            raise ValueError('Current CPC must be non-negative')
        
        # Convert to Decimal for precise calculation
        current_cpc_decimal = Decimal(str(current_cpc))
        target_roas_decimal = Decimal(str(target_roas))
        
        adjusted_cpc = current_cpc_decimal * (target_roas_decimal / 100)
        
        # Round to 2 decimal places, matching PHP's round() behavior
        return float(adjusted_cpc.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    
    @staticmethod
    def validate_bid_data(product_id: Union[int, str, None], 
                         current_cpc: Union[float, str, None], 
                         target_roas: Union[float, str, None]) -> List[str]:
        """
        Validate bid data parameters.
        
        Args:
            product_id: Product identifier
            current_cpc: Current cost per click
            target_roas: Target return on ad spend
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Validate product_id
        if product_id is None or product_id == '':
            errors.append('Invalid product ID')
        else:
            try:
                float(product_id)  # Check if numeric like in PHP
            except (ValueError, TypeError):
                errors.append('Invalid product ID')
        
        # Validate current_cpc
        try:
            cpc_value = float(current_cpc)
            if cpc_value < 0:
                errors.append('Invalid current CPC')
        except (ValueError, TypeError):
            errors.append('Invalid current CPC')
        
        # Validate target_roas
        try:
            roas_value = float(target_roas)
            if roas_value <= 0:
                errors.append('Invalid target ROAS')
        except (ValueError, TypeError):
            errors.append('Invalid target ROAS')
        
        return errors
