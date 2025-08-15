#!/usr/bin/env python3
"""
Script to create sample linked products for testing.
"""

from core.database import get_db_session
from core.models import Product, ProductLink
from core.services import ProductService

def create_linked_products():
    """Create some sample linked products."""
    
    session = get_db_session()
    try:
        # Get existing products
        products = session.query(Product).all()
        
        if len(products) < 2:
            print("Need at least 2 products to create links. Please run add_sample_products.py first.")
            return
        
        # Create some logical links
        # Example: Curtains -> Curtain Rods, Tiebacks
        curtain_products = [p for p in products if 'ستائر' in p.name.lower() or 'curtain' in p.name.lower()]
        other_products = [p for p in products if p not in curtain_products]
        
        if curtain_products and other_products:
            main_curtain = curtain_products[0]
            
            # Link curtains to other products as accessories
            for i, accessory in enumerate(other_products[:2]):  # Link to first 2 accessories
                # Check if link already exists
                existing_link = session.query(ProductLink).filter_by(
                    product_id=main_curtain.id,
                    linked_product_id=accessory.id
                ).first()
                
                if not existing_link:
                    link = ProductLink(
                        product_id=main_curtain.id,
                        linked_product_id=accessory.id,
                        link_type="accessory",
                        note=f"Recommended accessory for {main_curtain.name}"
                    )
                    session.add(link)
                    print(f"✅ Created link: {main_curtain.name} -> {accessory.name}")
                else:
                    print(f"⚠️  Link already exists: {main_curtain.name} -> {accessory.name}")
        
        session.commit()
        print(f"✅ Linked products setup complete!")
        
        # Show what links were created
        links = session.query(ProductLink).all()
        print(f"\n📋 Current product links:")
        for link in links:
            main_product = session.get(Product, link.product_id)
            linked_product = session.get(Product, link.linked_product_id)
            print(f"  • {main_product.name} -> {linked_product.name}")
            
    finally:
        session.close()

if __name__ == "__main__":
    create_linked_products()
