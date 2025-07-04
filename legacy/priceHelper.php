<?php

class PriceHelper {
    public static function calculateAdjustedCpc($currentCpc, $targetRoas) {
        if ($targetRoas <= 0) {
            throw new InvalidArgumentException('Target ROAS must be greater than 0');
        }
        
        if ($currentCpc < 0) {
            throw new InvalidArgumentException('Current CPC must be non-negative');
        }
        
        $adjustedCpc = $currentCpc * ($targetRoas / 100);
        return round($adjustedCpc, 2);
    }
    
    public static function validateBidData($productId, $currentCpc, $targetRoas) {
        $errors = [];
        
        if (empty($productId) || !is_numeric($productId)) {
            $errors[] = 'Invalid product ID';
        }
        
        if (!is_numeric($currentCpc) || $currentCpc < 0) {
            $errors[] = 'Invalid current CPC';
        }
        
        if (!is_numeric($targetRoas) || $targetRoas <= 0) {
            $errors[] = 'Invalid target ROAS';
        }
        
        return $errors;
    }
}

?>
