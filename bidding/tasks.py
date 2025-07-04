"""
Async tasks using Huey for daily budget audits and background processing
"""
from huey.contrib.djhuey import task
from django.utils import timezone
from datetime import timedelta
from .models import ProductBid


def daily_budget_audit():
    """
    Daily budget audit task that:
    - Fetches the latest 7 days of ProductBid rows
    - Flags any where abs(adjusted_cpc - current_cpc) > 0.20 * current_cpc
    - Prints a concise report to stdout
    
    Note: This is the actual implementation that can be called directly or as a task
    """
    # Calculate date range for the last 7 days
    seven_days_ago = timezone.now() - timedelta(days=7)
    
    # Fetch ProductBid records from the last 7 days
    recent_bids = ProductBid.objects.filter(
        calculated_at__gte=seven_days_ago
    ).order_by('product_id')
    
    if not recent_bids.exists():
        print("Daily Budget Audit: No bids found in the last 7 days")
        return {
            'total_bids': 0,
            'flagged_bids': 0,
            'audit_timestamp': timezone.now().isoformat()
        }
    
    flagged_bids = []
    total_bids = recent_bids.count()
    
    for bid in recent_bids:
        # Calculate the threshold (20% of current CPC)
        threshold = 0.20 * float(bid.current_cpc)
        
        # Calculate the difference between adjusted and current CPC
        cpc_difference = abs(float(bid.adjusted_cpc) - float(bid.current_cpc))
        
        if cpc_difference > threshold:
            flagged_bids.append({
                'bid_id': bid.id,
                'product_id': bid.product_id,
                'current_cpc': float(bid.current_cpc),
                'adjusted_cpc': float(bid.adjusted_cpc),
                'difference': cpc_difference,
                'threshold': threshold,
                'calculated_at': bid.calculated_at.strftime('%Y-%m-%d %H:%M:%S')
            })
    
    # Print concise report
    print("=" * 60)
    print("DAILY BUDGET AUDIT REPORT")
    print("=" * 60)
    print(f"Audit Period: {seven_days_ago.strftime('%Y-%m-%d %H:%M:%S')} to {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Bids Reviewed: {total_bids}")
    print(f"Flagged Bids: {len(flagged_bids)}")
    print("")
    
    if flagged_bids:
        print("FLAGGED BIDS (CPC difference > 20% of current CPC):")
        print("-" * 60)
        for bid in flagged_bids:
            print(f"Bid ID: {bid['bid_id']} | Product: {bid['product_id']}")
            print(f"  Current CPC: ${bid['current_cpc']:.2f}")
            print(f"  Adjusted CPC: ${bid['adjusted_cpc']:.2f}")
            print(f"  Difference: ${bid['difference']:.2f} (Threshold: ${bid['threshold']:.2f})")
            print(f"  Calculated: {bid['calculated_at']}")
            print("")
    else:
        print("No bids flagged - all CPC adjustments within acceptable limits.")
    
    print("=" * 60)
    print("Audit completed successfully")
    print("=" * 60)
    
    return {
        'total_bids': total_bids,
        'flagged_bids': len(flagged_bids),
        'audit_timestamp': timezone.now().isoformat()
    }


@task()
def daily_budget_audit_async():
    """
    Async wrapper for the daily budget audit task
    """
    return daily_budget_audit()
