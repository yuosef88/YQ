"""
Business calculation functions for quotations.
Implements the exact calculation rules specified in the requirements.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any
from core.models import UnitType, DiscountType


def calc_area(width: Decimal, height: Decimal) -> Decimal:
    """Calculate area from width and height, rounded to 3 decimal places."""
    if not width or not height:
        return Decimal('0.000')
    
    area = width * height
    return area.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)


def calc_total_area(area: Decimal, quantity: int) -> Decimal:
    """Calculate total area from area and quantity, rounded to 3 decimal places."""
    if not area or not quantity:
        return Decimal('0.000')
    
    total_area = area * Decimal(str(quantity))
    return total_area.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)


def get_base_qty(unit_type: UnitType, width: Decimal, height: Decimal, 
                 area: Decimal, total_area: Decimal, quantity: int) -> Decimal:
    """
    Determine the base quantity for pricing based on product unit type.
    
    Args:
        unit_type: Product's unit type (area/width/length/pcs)
        width: Item width in meters
        height: Item height in meters  
        area: Single item area (width * height)
        total_area: Total area (area * quantity)
        quantity: Number of items
        
    Returns:
        Base quantity to use for pricing calculation
    """
    if unit_type == UnitType.AREA:
        return total_area  # Use total_area to respect quantity
    elif unit_type == UnitType.WIDTH:
        return (width or Decimal('0')) * Decimal(str(quantity))
    elif unit_type == UnitType.LENGTH:
        return (height or Decimal('0')) * Decimal(str(quantity))
    elif unit_type == UnitType.PCS:
        return Decimal(str(quantity))
    else:
        return Decimal('0')


def get_effective_unit_price(base_price: Decimal, variation_price: Decimal = None) -> Decimal:
    """Get the effective unit price, preferring variation override."""
    if variation_price is not None:
        return variation_price
    return base_price or Decimal('0')


def apply_discount(base_amount: Decimal, discount_type: DiscountType, 
                  discount_value: Decimal) -> Decimal:
    """
    Apply discount to base amount, clamping result to minimum 0.
    
    Args:
        base_amount: Amount before discount
        discount_type: Percentage or fixed discount
        discount_value: Discount value (percentage or fixed amount)
        
    Returns:
        Amount after discount, minimum 0
    """
    if not discount_value:
        return base_amount
    
    if discount_type == DiscountType.PERCENT:
        discount_amount = base_amount * (discount_value / Decimal('100'))
        result = base_amount - discount_amount
    else:  # FIXED
        result = base_amount - discount_value
    
    # Clamp to minimum 0
    return max(result, Decimal('0'))


def calc_line_totals(width: Decimal, height: Decimal, quantity: int,
                    unit_type: UnitType, base_unit_price: Decimal,
                    variation_price: Decimal = None,
                    discount_type: DiscountType = DiscountType.FIXED,
                    discount_value: Decimal = Decimal('0'),
                    tax_rate: Decimal = Decimal('0.15')) -> Dict[str, Decimal]:
    """
    Calculate all line totals for a quote item.
    
    Returns:
        Dictionary with calculated values:
        - area: Item area (width * height)
        - total_area: Total area (area * quantity)
        - base_qty: Quantity used for pricing
        - unit_price: Effective unit price used
        - line_base: Base line amount before discount
        - line_total_ex_vat: Line total after discount, before VAT
        - vat_amount: VAT amount for this line
        - line_total_inc_vat: Final line total including VAT
    """
    # Calculate areas
    area = calc_area(width or Decimal('0'), height or Decimal('0'))
    total_area = calc_total_area(area, quantity or 1)
    
    # Get base quantity for pricing
    base_qty = get_base_qty(unit_type, width, height, area, total_area, quantity or 1)
    
    # Get effective unit price
    unit_price = get_effective_unit_price(base_unit_price, variation_price)
    
    # Calculate base line amount
    line_base = base_qty * unit_price
    
    # Apply item discount
    line_total_ex_vat = apply_discount(line_base, discount_type, discount_value)
    
    # Calculate VAT
    vat_amount = (line_total_ex_vat * tax_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    # Final line total
    line_total_inc_vat = line_total_ex_vat + vat_amount
    
    return {
        'area': area,
        'total_area': total_area,
        'base_qty': base_qty,
        'unit_price': unit_price,
        'line_base': line_base,
        'line_total_ex_vat': line_total_ex_vat.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        'vat_amount': vat_amount,
        'line_total_inc_vat': line_total_inc_vat.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    }


def calc_quotation_totals(items_data: List[Dict[str, Any]],
                         header_discount_type: DiscountType = DiscountType.FIXED,
                         header_discount_value: Decimal = Decimal('0'),
                         tax_rate: Decimal = Decimal('0.15')) -> Dict[str, Decimal]:
    """
    Calculate quotation totals from line items.
    
    Args:
        items_data: List of item dictionaries with 'line_total_ex_vat' values
        header_discount_type: Header-level discount type
        header_discount_value: Header-level discount value
        tax_rate: Tax rate for VAT calculation
        
    Returns:
        Dictionary with quotation totals:
        - items_subtotal_ex_vat: Sum of all line totals before header discount
        - total_item_discounts: Sum of all per-item discounts (for display)
        - discount_header: Header discount amount
        - discounted_ex_vat: Subtotal after header discount
        - vat_amount: VAT on discounted amount
        - grand_total: Final total including VAT
    """
    # Sum up line totals
    items_subtotal_ex_vat = sum(
        Decimal(str(item.get('line_total_ex_vat', 0))) for item in items_data
    )
    
    # Calculate total item discounts (for display only)
    total_item_discounts = sum(
        Decimal(str(item.get('discount_amount', 0))) for item in items_data
    )
    
    # Apply header discount
    if header_discount_type == DiscountType.PERCENT:
        discount_header = items_subtotal_ex_vat * (header_discount_value / Decimal('100'))
    else:  # FIXED
        discount_header = header_discount_value
    
    # Calculate discounted subtotal
    discounted_ex_vat = max(items_subtotal_ex_vat - discount_header, Decimal('0'))
    
    # Calculate VAT on discounted amount
    vat_amount = (discounted_ex_vat * tax_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    # Grand total
    grand_total = discounted_ex_vat + vat_amount
    
    return {
        'items_subtotal_ex_vat': items_subtotal_ex_vat.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        'total_item_discounts': total_item_discounts.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        'discount_header': discount_header.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        'discounted_ex_vat': discounted_ex_vat.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        'vat_amount': vat_amount,
        'grand_total': grand_total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    }
