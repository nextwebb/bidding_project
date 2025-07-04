from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import ProductBid
from .price_helper import PriceHelper
from decimal import Decimal


@api_view(['POST'])
def bid_endpoint(request):
    """
    POST /api/bid/ endpoint that calculates adjusted CPC
    
    Accepts: {product_id, current_cpc, target_roas}
    Returns: {adjusted_cpc}
    """
    # Extract data from request
    product_id = request.data.get('product_id')
    current_cpc = request.data.get('current_cpc')
    target_roas = request.data.get('target_roas')
    
    # Validate input data using legacy helper
    errors = PriceHelper.validate_bid_data(product_id, current_cpc, target_roas)
    if errors:
        return Response(
            {'errors': errors}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Calculate adjusted CPC using legacy helper
        adjusted_cpc = PriceHelper.calculate_adjusted_cpc(
            float(current_cpc), 
            float(target_roas)
        )
        
        # Persist to database
        product_bid = ProductBid.objects.create(
            product_id=int(product_id),
            current_cpc=Decimal(str(current_cpc)),
            target_roas=Decimal(str(target_roas)),
            adjusted_cpc=Decimal(str(adjusted_cpc))
        )
        
        return Response({
            'adjusted_cpc': adjusted_cpc,
            'bid_id': product_bid.id
        })
        
    except ValueError as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
