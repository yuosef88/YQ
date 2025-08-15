"""
Add sample products for testing the new quotation system.
"""

from decimal import Decimal
from core.database import get_db_session
from core.models import Product, ProductVariation, Customer, UnitType, CustomerType
from core.services import ProductService, CustomerService


def add_sample_data():
    """Add sample products and customers for testing."""
    print("Adding sample data...")
    
    # Add sample customers
    customers_data = [
        {
            'name': 'أحمد محمد',
            'phone': '0501234567',
            'email': 'ahmed@example.com',
            'type': CustomerType.INDIVIDUAL
        },
        {
            'name': 'شركة النور للديكور',
            'phone': '0119876543',
            'email': 'info@alnoor.com',
            'type': CustomerType.COMPANY,
            'company_name': 'شركة النور للديكور',
            'company_vat': '300123456789003'
        },
        {
            'name': 'فاطمة أحمد',
            'phone': '0551234567',
            'email': 'fatima@example.com',
            'type': CustomerType.INDIVIDUAL
        }
    ]
    
    print("Creating customers...")
    for customer_data in customers_data:
        try:
            CustomerService.create_customer(**customer_data)
            print(f"✓ Created customer: {customer_data['name']}")
        except Exception as e:
            print(f"✗ Error creating customer {customer_data['name']}: {e}")
    
    # Add sample products
    products_data = [
        {
            'name': 'ستائر حريرية فاخرة',
            'category': 'ستائر',
            'unit_type': UnitType.AREA,
            'base_unit_price': Decimal('320.00')
        },
        {
            'name': 'ستائر قطنية عادية',
            'category': 'ستائر',
            'unit_type': UnitType.AREA,
            'base_unit_price': Decimal('150.00')
        },
        {
            'name': 'ستائر بلاك آوت',
            'category': 'ستائر',
            'unit_type': UnitType.AREA,
            'base_unit_price': Decimal('280.00')
        },
        {
            'name': 'قضبان ستائر معدنية',
            'category': 'إكسسوارات',
            'unit_type': UnitType.LENGTH,
            'base_unit_price': Decimal('45.00')
        },
        {
            'name': 'حلقات ستائر',
            'category': 'إكسسوارات',
            'unit_type': UnitType.PCS,
            'base_unit_price': Decimal('5.00')
        },
        {
            'name': 'ستائر رول أب',
            'category': 'ستائر',
            'unit_type': UnitType.AREA,
            'base_unit_price': Decimal('200.00')
        }
    ]
    
    print("Creating products...")
    created_products = []
    for product_data in products_data:
        try:
            product = ProductService.create_product(**product_data)
            created_products.append(product)
            print(f"✓ Created product: {product_data['name']}")
        except Exception as e:
            print(f"✗ Error creating product {product_data['name']}: {e}")
    
    # Add variations for some products
    if created_products:
        print("Adding product variations...")
        
        # Add variations for the first product (silk curtains)
        silk_curtains = created_products[0]
        variations_data = [
            {'name': 'أحمر', 'unit_price_override': Decimal('350.00')},
            {'name': 'أزرق', 'unit_price_override': None},
            {'name': 'ذهبي', 'unit_price_override': Decimal('380.00')},
            {'name': 'أبيض', 'unit_price_override': None},
        ]
        
        for var_data in variations_data:
            try:
                ProductService.add_product_variation(silk_curtains.id, **var_data)
                print(f"✓ Added variation: {var_data['name']} for {silk_curtains.name}")
            except Exception as e:
                print(f"✗ Error adding variation {var_data['name']}: {e}")
        
        # Add variations for blackout curtains
        if len(created_products) >= 3:
            blackout_curtains = created_products[2]
            blackout_variations = [
                {'name': 'أسود', 'unit_price_override': None},
                {'name': 'رمادي', 'unit_price_override': Decimal('290.00')},
                {'name': 'بني', 'unit_price_override': Decimal('285.00')},
            ]
            
            for var_data in blackout_variations:
                try:
                    ProductService.add_product_variation(blackout_curtains.id, **var_data)
                    print(f"✓ Added variation: {var_data['name']} for {blackout_curtains.name}")
                except Exception as e:
                    print(f"✗ Error adding variation {var_data['name']}: {e}")
        
        # Add product links (accessories to curtains)
        if len(created_products) >= 5:
            try:
                # Link curtain rods to silk curtains
                ProductService.add_product_link(
                    silk_curtains.id, 
                    created_products[3].id,  # curtain rods
                    link_type="accessory",
                    note="Recommended for silk curtains"
                )
                print("✓ Linked curtain rods to silk curtains")
                
                # Link rings to curtain rods
                ProductService.add_product_link(
                    created_products[3].id,  # curtain rods
                    created_products[4].id,  # rings
                    link_type="accessory",
                    note="Required for installation"
                )
                print("✓ Linked rings to curtain rods")
                
            except Exception as e:
                print(f"✗ Error creating product links: {e}")
    
    print("Sample data added successfully!")


if __name__ == "__main__":
    add_sample_data()


