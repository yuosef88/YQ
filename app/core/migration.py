"""
Database migration system for upgrading from old schema to new schema.
Handles data migration and backfilling of new fields.
"""

import json
import shutil
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from core.database import get_db_session, init_db
from core.models import (
    Customer, Product, Quotation, QuoteItem, CompanySettings,
    CustomerType, UnitType, QuotationStatus, DiscountType, Currency
)
from core.paths import app_paths
from core.serial import generate_quotation_serial


def backup_existing_data():
    """Backup existing data before migration."""
    print("Backing up existing data...")
    
    # Check if old database exists
    old_db_path = Path("data/app.db")
    if not old_db_path.exists():
        print("No existing database found. Starting fresh.")
        return None
    
    # Create backup directory
    backup_dir = Path("backup_migration")
    backup_dir.mkdir(exist_ok=True)
    
    # Copy old database
    backup_db_path = backup_dir / f"app_old_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(old_db_path, backup_db_path)
    print(f"Database backed up to: {backup_db_path}")
    
    # Export data to JSON for migration
    old_engine = create_engine(f"sqlite:///{old_db_path}")
    old_session = sessionmaker(bind=old_engine)()
    
    try:
        # Export customers
        customers = old_session.execute(text("SELECT * FROM customers")).fetchall()
        customers_data = [dict(row._mapping) for row in customers]
        
        # Export products
        products = old_session.execute(text("SELECT * FROM products")).fetchall()
        products_data = [dict(row._mapping) for row in products]
        
        # Export quotations
        quotations = old_session.execute(text("SELECT * FROM quotations")).fetchall()
        quotations_data = [dict(row._mapping) for row in quotations]
        
        # Export quote items
        quote_items = old_session.execute(text("SELECT * FROM quote_items")).fetchall()
        quote_items_data = [dict(row._mapping) for row in quote_items]
        
        # Export company settings if exists
        try:
            company_settings = old_session.execute(text("SELECT * FROM company_settings")).fetchall()
            company_settings_data = [dict(row._mapping) for row in company_settings]
        except:
            company_settings_data = []
        
        # Save to JSON files
        with open(backup_dir / "customers.json", 'w', encoding='utf-8') as f:
            json.dump(customers_data, f, indent=2, default=str)
        
        with open(backup_dir / "products.json", 'w', encoding='utf-8') as f:
            json.dump(products_data, f, indent=2, default=str)
        
        with open(backup_dir / "quotations.json", 'w', encoding='utf-8') as f:
            json.dump(quotations_data, f, indent=2, default=str)
        
        with open(backup_dir / "quote_items.json", 'w', encoding='utf-8') as f:
            json.dump(quote_items_data, f, indent=2, default=str)
        
        with open(backup_dir / "company_settings.json", 'w', encoding='utf-8') as f:
            json.dump(company_settings_data, f, indent=2, default=str)
        
        print(f"Data exported to JSON files in: {backup_dir}")
        
        return {
            'customers': customers_data,
            'products': products_data,
            'quotations': quotations_data,
            'quote_items': quote_items_data,
            'company_settings': company_settings_data
        }
        
    finally:
        old_session.close()


def migrate_customers(session, customers_data):
    """Migrate customer data to new schema."""
    print(f"Migrating {len(customers_data)} customers...")
    
    for customer_data in customers_data:
        customer = Customer(
            id=customer_data.get('id'),
            name=customer_data.get('name', ''),
            email=customer_data.get('email', ''),
            phone=customer_data.get('phone', ''),
            address=customer_data.get('address', ''),
            # New fields with defaults
            type=CustomerType.INDIVIDUAL,  # Default for existing customers
            company_name=None,
            company_vat=None,
            company_address=None,
            created_at=datetime.fromisoformat(customer_data.get('created_at', datetime.now().isoformat()))
        )
        session.add(customer)
    
    session.commit()
    print("Customers migrated successfully.")


def migrate_products(session, products_data):
    """Migrate product data to new schema."""
    print(f"Migrating {len(products_data)} products...")
    
    for product_data in products_data:
        # Handle currency field
        currency_str = product_data.get('currency', 'SAR')
        try:
            currency = Currency(currency_str)
        except ValueError:
            currency = Currency.SAR
        
        product = Product(
            id=product_data.get('id'),
            name=product_data.get('name', ''),
            category=product_data.get('category', ''),
            # New fields
            unit_type=UnitType.AREA,  # Default for existing products
            base_unit_price=Decimal(str(product_data.get('price', 0))),
            currency=currency,
            notes=None,
            created_at=datetime.fromisoformat(product_data.get('created_at', datetime.now().isoformat()))
        )
        session.add(product)
    
    session.commit()
    print("Products migrated successfully.")


def migrate_quotations(session, quotations_data):
    """Migrate quotation data to new schema."""
    print(f"Migrating {len(quotations_data)} quotations...")
    
    for quotation_data in quotations_data:
        # Generate serial number if not present
        serial = quotation_data.get('serial_number')
        if not serial:
            # Extract year from created_at or use current year
            created_at_str = quotation_data.get('created_at', datetime.now().isoformat())
            created_at = datetime.fromisoformat(created_at_str)
            serial = generate_quotation_serial(created_at.year)
        
        quotation = Quotation(
            id=quotation_data.get('id'),
            serial_number=serial,
            customer_id=quotation_data.get('customer_id'),
            # Status handling
            status=QuotationStatus.DRAFT,  # Default for existing quotations
            # Discount and tax defaults
            header_discount_type=DiscountType.FIXED,
            header_discount_value=Decimal('0.00'),
            tax_rate=Decimal('0.15'),
            # Totals - will be recalculated later
            subtotal_ex_vat=Decimal(str(quotation_data.get('total_amount', 0))),
            discount_header=Decimal('0.00'),
            discounted_ex_vat=Decimal(str(quotation_data.get('final_amount', quotation_data.get('total_amount', 0)))),
            vat_amount=Decimal('0.00'),  # Will be recalculated
            grand_total=Decimal(str(quotation_data.get('final_amount', quotation_data.get('total_amount', 0)))),
            notes=quotation_data.get('notes', ''),
            created_at=datetime.fromisoformat(quotation_data.get('created_at', datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(quotation_data.get('updated_at', datetime.now().isoformat()))
        )
        session.add(quotation)
    
    session.commit()
    print("Quotations migrated successfully.")


def migrate_quote_items(session, quote_items_data):
    """Migrate quote item data to new schema."""
    print(f"Migrating {len(quote_items_data)} quote items...")
    
    for item_data in quote_items_data:
        # Calculate area if width/height available
        width = Decimal(str(item_data.get('width', 0)))
        height = Decimal(str(item_data.get('height', 0)))
        area = width * height if width and height else Decimal('0')
        quantity = int(item_data.get('quantity', 1))
        total_area = area * quantity
        
        # Get unit price
        unit_price = Decimal(str(item_data.get('unit_price', 0)))
        line_total = Decimal(str(item_data.get('line_total', unit_price * quantity)))
        
        quote_item = QuoteItem(
            id=item_data.get('id'),
            quotation_id=item_data.get('quotation_id'),
            product_id=item_data.get('product_id'),
            # New fields
            product_variation_id=None,
            color_text=None,
            width=width if width > 0 else None,
            height=height if height > 0 else None,
            area=area,
            quantity=quantity,
            total_area=total_area,
            unit_price=unit_price,
            discount_type=DiscountType.FIXED,
            discount_value=Decimal('0.00'),
            line_total_ex_vat=line_total,
            vat_amount=line_total * Decimal('0.15'),  # Estimate VAT
            line_total_inc_vat=line_total * Decimal('1.15'),
            notes=None,
            created_at=datetime.fromisoformat(item_data.get('created_at', datetime.now().isoformat()))
        )
        session.add(quote_item)
    
    session.commit()
    print("Quote items migrated successfully.")


def migrate_company_settings(session, company_settings_data):
    """Migrate company settings or create defaults."""
    if company_settings_data:
        print("Migrating company settings...")
        settings_data = company_settings_data[0]  # Assume single settings record
        
        settings = CompanySettings(
            company_name=settings_data.get('company_name', 'Adhlal'),
            logo_path=settings_data.get('logo_path', ''),
            address=settings_data.get('address', ''),
            phone=settings_data.get('phone', ''),
            email=settings_data.get('email', ''),
            website=settings_data.get('website', ''),
            default_currency=Currency.SAR,
            default_tax_rate=Decimal(str(settings_data.get('tax_rate', 0.15))),
            clipboard_copy_format='"{ItemName} {Color} {W} {H}"'
        )
    else:
        print("Creating default company settings...")
        settings = CompanySettings(
            company_name="Adhlal",
            default_currency=Currency.SAR,
            default_tax_rate=Decimal('0.15'),
            clipboard_copy_format='"{ItemName} {Color} {W} {H}"'
        )
    
    session.add(settings)
    session.commit()
    print("Company settings migrated successfully.")


def run_migration():
    """Run the complete migration process."""
    print("=" * 60)
    print("STARTING DATABASE MIGRATION")
    print("=" * 60)
    
    # Step 1: Backup existing data
    backup_data = backup_existing_data()
    
    # Step 2: Initialize new database structure
    print("\nInitializing new database structure...")
    init_db()
    
    # Step 3: Migrate data if backup exists
    if backup_data:
        session = get_db_session()
        try:
            migrate_customers(session, backup_data['customers'])
            migrate_products(session, backup_data['products'])
            migrate_quotations(session, backup_data['quotations'])
            migrate_quote_items(session, backup_data['quote_items'])
            migrate_company_settings(session, backup_data['company_settings'])
            
            print("\n" + "=" * 60)
            print("MIGRATION COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            print(f"Database location: {app_paths.database_path}")
            print(f"Media directory: {app_paths.media_dir}")
            
        except Exception as e:
            print(f"\nMigration error: {e}")
            session.rollback()
            raise
        finally:
            session.close()
    else:
        # No existing data, just set up default company settings
        session = get_db_session()
        try:
            migrate_company_settings(session, [])
        finally:
            session.close()
    
    print("\nMigration process complete!")


if __name__ == "__main__":
    run_migration()
