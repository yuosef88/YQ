"""
Enhanced business services for the Curtain Quotation System.
Handles all business logic and database operations.
"""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime, date
from sqlalchemy.orm import joinedload
from sqlalchemy import and_, or_, desc

from core.database import get_db_session
from core.models import (
    Customer, Product, ProductVariation, ProductLink, Employee,
    Quotation, QuoteItem, Assignment, Payment, CompanySettings,
    CustomerType, UnitType, QuotationStatus, AssignmentType, AssignmentStatus,
    PaymentMethod, DiscountType
)
from core.serial import generate_quotation_serial
from core.calculations import calc_line_totals, calc_quotation_totals
from core.paths import app_paths


class CustomerService:
    """Service for customer operations."""
    
    @staticmethod
    def get_all_customers() -> List[Customer]:
        """Get all customers."""
        session = get_db_session()
        try:
            return session.query(Customer).order_by(Customer.name).all()
        finally:
            session.close()
    
    @staticmethod
    def get_customer_by_id(customer_id: int) -> Optional[Customer]:
        """Get customer by ID."""
        session = get_db_session()
        try:
            return session.query(Customer).filter(Customer.id == customer_id).first()
        finally:
            session.close()
    
    @staticmethod
    def search_customers(query: str = "", phone: str = "") -> List[Customer]:
        """Search customers by name, email, or phone."""
        session = get_db_session()
        try:
            filters = []
            
            if query:
                filters.append(
                    or_(
                        Customer.name.contains(query),
                        Customer.email.contains(query),
                        Customer.company_name.contains(query)
                    )
                )
            
            if phone:
                filters.append(Customer.phone.contains(phone))
            
            if filters:
                return session.query(Customer).filter(and_(*filters)).order_by(Customer.name).all()
            else:
                return CustomerService.get_all_customers()
        finally:
            session.close()
    
    @staticmethod
    def create_customer(name: str, email: str = "", phone: str = "", address: str = "",
                       customer_type: CustomerType = CustomerType.INDIVIDUAL,
                       company_name: str = "", company_vat: str = "", 
                       company_address: str = "") -> Customer:
        """Create a new customer."""
        session = get_db_session()
        try:
            customer = Customer(
                name=name,
                email=email,
                phone=phone,
                address=address,
                type=customer_type,
                company_name=company_name,
                company_vat=company_vat,
                company_address=company_address
            )
            session.add(customer)
            session.commit()
            session.refresh(customer)
            return customer
        finally:
            session.close()
    
    @staticmethod
    def update_customer(customer_id: int, **kwargs) -> Optional[Customer]:
        """Update an existing customer."""
        session = get_db_session()
        try:
            customer = session.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                return None
            
            for key, value in kwargs.items():
                if hasattr(customer, key):
                    setattr(customer, key, value)
            
            session.commit()
            session.refresh(customer)
            return customer
        finally:
            session.close()
    
    @staticmethod
    def delete_customer(customer_id: int) -> bool:
        """Delete a customer if they have no quotations."""
        session = get_db_session()
        try:
            customer = session.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                return False
            
            # Check if customer has quotations
            quote_count = session.query(Quotation).filter(Quotation.customer_id == customer_id).count()
            if quote_count > 0:
                raise ValueError("Cannot delete customer with existing quotations")
            
            session.delete(customer)
            session.commit()
            return True
        finally:
            session.close()


class ProductService:
    """Service for product operations."""
    
    @staticmethod
    def get_all_products() -> List[Product]:
        """Get all products with their variations."""
        session = get_db_session()
        try:
            return (
                session.query(Product)
                .options(joinedload(Product.variations))
                .order_by(Product.name)
                .all()
            )
        finally:
            session.close()
    
    @staticmethod
    def get_product_by_id(product_id: int) -> Optional[Product]:
        """Get product by ID with variations and links."""
        session = get_db_session()
        try:
            return (
                session.query(Product)
                .options(
                    joinedload(Product.variations),
                    joinedload(Product.linked_products).joinedload(ProductLink.linked_product)
                )
                .filter(Product.id == product_id)
                .first()
            )
        finally:
            session.close()
    
    @staticmethod
    def search_products(query: str = "") -> List[Product]:
        """Search products by name or category."""
        session = get_db_session()
        try:
            if query:
                return (
                    session.query(Product)
                    .options(joinedload(Product.variations))
                    .filter(
                        or_(
                            Product.name.contains(query),
                            Product.category.contains(query)
                        )
                    )
                    .order_by(Product.name)
                    .all()
                )
            else:
                return ProductService.get_all_products()
        finally:
            session.close()
    
    @staticmethod
    def create_product(name: str, category: str = "", unit_type: UnitType = UnitType.AREA,
                      base_unit_price: Decimal = Decimal('0'), notes: str = "") -> Product:
        """Create a new product."""
        session = get_db_session()
        try:
            product = Product(
                name=name,
                category=category,
                unit_type=unit_type,
                base_unit_price=base_unit_price,
                notes=notes
            )
            session.add(product)
            session.commit()
            session.refresh(product)
            return product
        finally:
            session.close()
    
    @staticmethod
    def add_product_variation(product_id: int, name: str, unit_price_override: Decimal = None,
                             sku: str = "", image_path: str = "") -> Optional[ProductVariation]:
        """Add a variation to a product."""
        session = get_db_session()
        try:
            # Convert absolute path to relative if needed
            if image_path:
                image_path = app_paths.get_relative_media_path(image_path)
            
            variation = ProductVariation(
                product_id=product_id,
                name=name,
                unit_price_override=unit_price_override,
                sku=sku,
                image_path=image_path
            )
            session.add(variation)
            session.commit()
            session.refresh(variation)
            return variation
        finally:
            session.close()
    
    @staticmethod
    def add_product_link(product_id: int, linked_product_id: int, 
                        link_type: str = "", note: str = "") -> Optional[ProductLink]:
        """Link two products together."""
        session = get_db_session()
        try:
            # Check if link already exists
            existing = (
                session.query(ProductLink)
                .filter(
                    and_(
                        ProductLink.product_id == product_id,
                        ProductLink.linked_product_id == linked_product_id
                    )
                )
                .first()
            )
            
            if existing:
                return existing
            
            link = ProductLink(
                product_id=product_id,
                linked_product_id=linked_product_id,
                link_type=link_type,
                note=note
            )
            session.add(link)
            session.commit()
            session.refresh(link)
            return link
        finally:
            session.close()
    
    @staticmethod
    def get_product_variations(product_id: int) -> List[ProductVariation]:
        """Get all variations for a product."""
        session = get_db_session()
        try:
            return (
                session.query(ProductVariation)
                .filter(ProductVariation.product_id == product_id)
                .order_by(ProductVariation.name)
                .all()
            )
        finally:
            session.close()
    
    @staticmethod
    def get_linked_products(product_id: int) -> List[ProductLink]:
        """Get all linked products for a product."""
        session = get_db_session()
        try:
            return (
                session.query(ProductLink)
                .filter(ProductLink.product_id == product_id)
                .all()
            )
        finally:
            session.close()
    
    @staticmethod
    def create_product_variation(product_id: int, name: str, unit_price_override: Decimal = None,
                                sku: str = None, image_path: str = None) -> ProductVariation:
        """Create a product variation."""
        session = get_db_session()
        try:
            variation = ProductVariation(
                product_id=product_id,
                name=name,
                unit_price_override=unit_price_override,
                sku=sku,
                image_path=image_path
            )
            session.add(variation)
            session.commit()
            session.refresh(variation)
            return variation
        finally:
            session.close()
    
    @staticmethod
    def create_product_link(product_id: int, linked_product_id: int, 
                           link_type: str = "suggested", note: str = None) -> ProductLink:
        """Create a product link."""
        session = get_db_session()
        try:
            # Check if link already exists
            existing = (
                session.query(ProductLink)
                .filter(
                    and_(
                        ProductLink.product_id == product_id,
                        ProductLink.linked_product_id == linked_product_id
                    )
                )
                .first()
            )
            
            if existing:
                return existing
            
            link = ProductLink(
                product_id=product_id,
                linked_product_id=linked_product_id,
                link_type=link_type,
                note=note
            )
            session.add(link)
            session.commit()
            session.refresh(link)
            return link
        finally:
            session.close()
    
    @staticmethod
    def clear_product_variations(product_id: int) -> bool:
        """Clear all variations for a product."""
        session = get_db_session()
        try:
            session.query(ProductVariation).filter(
                ProductVariation.product_id == product_id
            ).delete()
            session.commit()
            return True
        finally:
            session.close()
    
    @staticmethod
    def clear_product_links(product_id: int) -> bool:
        """Clear all links for a product."""
        session = get_db_session()
        try:
            session.query(ProductLink).filter(
                ProductLink.product_id == product_id
            ).delete()
            session.commit()
            return True
        finally:
            session.close()
    
    @staticmethod
    def update_product(product_id: int, name: str = None, category: str = None,
                      unit_type: UnitType = None, base_unit_price: Decimal = None,
                      notes: str = None) -> bool:
        """Update a product."""
        session = get_db_session()
        try:
            product = session.query(Product).filter(Product.id == product_id).first()
            if not product:
                return False
            
            if name is not None:
                product.name = name
            if category is not None:
                product.category = category
            if unit_type is not None:
                product.unit_type = unit_type
            if base_unit_price is not None:
                product.base_unit_price = base_unit_price
            if notes is not None:
                product.notes = notes
            
            session.commit()
            return True
        finally:
            session.close()
    
    @staticmethod
    def delete_product(product_id: int) -> bool:
        """Delete a product."""
        session = get_db_session()
        try:
            product = session.query(Product).filter(Product.id == product_id).first()
            if not product:
                return False
            
            session.delete(product)
            session.commit()
            return True
        finally:
            session.close()


class EmployeeService:
    """Service for employee operations."""
    
    @staticmethod
    def get_all_employees(active_only: bool = True) -> List[Employee]:
        """Get all employees."""
        session = get_db_session()
        try:
            query = session.query(Employee)
            if active_only:
                query = query.filter(Employee.active == True)
            return query.order_by(Employee.full_name).all()
        finally:
            session.close()
    
    @staticmethod
    def create_employee(full_name: str, phone: str = "", role: str = "") -> Employee:
        """Create a new employee."""
        session = get_db_session()
        try:
            employee = Employee(
                full_name=full_name,
                phone=phone,
                role=role
            )
            session.add(employee)
            session.commit()
            session.refresh(employee)
            return employee
        finally:
            session.close()


class QuotationService:
    """Service for quotation operations."""
    
    @staticmethod
    def get_all_quotations() -> List[Quotation]:
        """Get all quotations with customer data."""
        session = get_db_session()
        try:
            return (
                session.query(Quotation)
                .options(joinedload(Quotation.customer))
                .order_by(desc(Quotation.created_at))
                .all()
            )
        finally:
            session.close()
    
    @staticmethod
    def get_quotation_by_id(quotation_id: int) -> Optional[Quotation]:
        """Get quotation by ID with all related data."""
        session = get_db_session()
        try:
            return (
                session.query(Quotation)
                .options(
                    joinedload(Quotation.customer),
                    joinedload(Quotation.items).joinedload(QuoteItem.product),
                    joinedload(Quotation.items).joinedload(QuoteItem.product_variation),
                    joinedload(Quotation.payments),
                    joinedload(Quotation.assignments)
                )
                .filter(Quotation.id == quotation_id)
                .first()
            )
        finally:
            session.close()
    
    @staticmethod
    def search_quotations(customer_phone: str = "", date_from: date = None,
                         date_to: date = None, status: QuotationStatus = None) -> List[Quotation]:
        """Search quotations with filters."""
        session = get_db_session()
        try:
            query = (
                session.query(Quotation)
                .options(joinedload(Quotation.customer))
                .join(Customer)
            )
            
            filters = []
            
            if customer_phone:
                filters.append(Customer.phone.contains(customer_phone))
            
            if date_from:
                filters.append(Quotation.created_at >= datetime.combine(date_from, datetime.min.time()))
            
            if date_to:
                filters.append(Quotation.created_at <= datetime.combine(date_to, datetime.max.time()))
            
            if status:
                filters.append(Quotation.status == status)
            
            if filters:
                query = query.filter(and_(*filters))
            
            return query.order_by(desc(Quotation.created_at)).all()
        finally:
            session.close()
    
    @staticmethod
    def create_quotation(customer_id: int, notes: str = "") -> Quotation:
        """Create a new quotation."""
        session = get_db_session()
        try:
            # Generate serial number
            serial = generate_quotation_serial()
            
            quotation = Quotation(
                serial_number=serial,
                customer_id=customer_id,
                notes=notes
            )
            session.add(quotation)
            session.commit()
            session.refresh(quotation)
            return quotation
        finally:
            session.close()
    
    @staticmethod
    def add_quote_item(quotation_id: int, product_id: int, width: Decimal = None,
                      height: Decimal = None, quantity: int = 1,
                      product_variation_id: int = None, color_text: str = "",
                      unit_price_override: Decimal = None, notes: str = "",
                      discount_type: DiscountType = DiscountType.FIXED,
                      discount_value: Decimal = Decimal('0')) -> Optional[QuoteItem]:
        """Add an item to a quotation."""
        session = get_db_session()
        try:
            # Get the quotation and product
            quotation = session.query(Quotation).filter(Quotation.id == quotation_id).first()
            if not quotation:
                return None
            
            product = (
                session.query(Product)
                .options(joinedload(Product.variations))
                .filter(Product.id == product_id)
                .first()
            )
            if not product:
                return None
            
            # Get variation if specified
            variation = None
            if product_variation_id:
                variation = session.query(ProductVariation).filter(
                    ProductVariation.id == product_variation_id
                ).first()
            
            # Determine effective unit price
            if unit_price_override is not None:
                unit_price = unit_price_override
            elif variation and variation.unit_price_override:
                unit_price = variation.unit_price_override
            else:
                unit_price = product.base_unit_price
            
            # Calculate line totals with discount
            totals = calc_line_totals(
                width=width or Decimal('0'),
                height=height or Decimal('0'),
                quantity=quantity,
                unit_type=product.unit_type,
                base_unit_price=product.base_unit_price,
                variation_price=variation.unit_price_override if variation else None,
                discount_type=discount_type,
                discount_value=discount_value,
                tax_rate=quotation.tax_rate
            )
            
            # Create quote item
            quote_item = QuoteItem(
                quotation_id=quotation_id,
                product_id=product_id,
                product_variation_id=product_variation_id,
                color_text=color_text,
                width=width,
                height=height,
                area=totals['area'],
                quantity=quantity,
                total_area=totals['total_area'],
                unit_price=totals['unit_price'],
                discount_type=discount_type,
                discount_value=discount_value,
                line_total_ex_vat=totals['line_total_ex_vat'],
                vat_amount=totals['vat_amount'],
                line_total_inc_vat=totals['line_total_inc_vat'],
                notes=notes
            )
            
            session.add(quote_item)
            session.commit()
            
            # Recalculate quotation totals
            QuotationService._recalculate_quotation_totals(quotation_id, session)
            
            session.refresh(quote_item)
            return quote_item
        finally:
            session.close()
    
    @staticmethod
    def _recalculate_quotation_totals(quotation_id: int, session):
        """Recalculate and update quotation totals."""
        quotation = session.query(Quotation).filter(Quotation.id == quotation_id).first()
        if not quotation:
            return
        
        # Get all items
        items = session.query(QuoteItem).filter(QuoteItem.quotation_id == quotation_id).all()
        
        # Prepare items data for calculation
        items_data = [
            {
                'line_total_ex_vat': item.line_total_ex_vat,
                'discount_amount': Decimal('0')  # Individual item discounts if implemented
            }
            for item in items
        ]
        
        # Calculate totals
        totals = calc_quotation_totals(
            items_data=items_data,
            header_discount_type=quotation.header_discount_type,
            header_discount_value=quotation.header_discount_value,
            tax_rate=quotation.tax_rate
        )
        
        # Update quotation
        quotation.subtotal_ex_vat = totals['items_subtotal_ex_vat']
        quotation.discount_header = totals['discount_header']
        quotation.discounted_ex_vat = totals['discounted_ex_vat']
        quotation.vat_amount = totals['vat_amount']
        quotation.grand_total = totals['grand_total']
        
        session.commit()
    
    @staticmethod
    def update_quotation_totals(quotation_id: int):
        """Public method to recalculate quotation totals."""
        session = get_db_session()
        try:
            QuotationService._recalculate_quotation_totals(quotation_id, session)
        finally:
            session.close()
    
    @staticmethod
    def update_quotation_status(quotation_id: int, status: QuotationStatus) -> bool:
        """Update quotation status."""
        session = get_db_session()
        try:
            quotation = session.query(Quotation).filter(Quotation.id == quotation_id).first()
            if not quotation:
                return False
            
            quotation.status = status
            quotation.updated_at = datetime.utcnow()
            session.commit()
            return True
        finally:
            session.close()


class PaymentService:
    """Service for payment operations."""
    
    @staticmethod
    def add_payment(quotation_id: int, amount: Decimal, payment_date: date,
                   method: PaymentMethod, reference: str = "", notes: str = "") -> Optional[Payment]:
        """Add a payment to a quotation."""
        session = get_db_session()
        try:
            payment = Payment(
                quotation_id=quotation_id,
                date=payment_date,
                amount=amount,
                method=method,
                reference=reference,
                notes=notes
            )
            session.add(payment)
            session.commit()
            session.refresh(payment)
            return payment
        finally:
            session.close()
    
    @staticmethod
    def get_quotation_payment_summary(quotation_id: int) -> Dict[str, Decimal]:
        """Get payment summary for a quotation."""
        session = get_db_session()
        try:
            quotation = session.query(Quotation).filter(Quotation.id == quotation_id).first()
            if not quotation:
                return {'grand_total': Decimal('0'), 'paid_total': Decimal('0'), 'balance': Decimal('0')}
            
            payments = session.query(Payment).filter(Payment.quotation_id == quotation_id).all()
            paid_total = sum(payment.amount for payment in payments)
            balance = quotation.grand_total - paid_total
            
            return {
                'grand_total': quotation.grand_total,
                'paid_total': paid_total,
                'balance': balance
            }
        finally:
            session.close()


class AssignmentService:
    """Service for assignment operations."""
    
    @staticmethod
    def create_assignment(quotation_id: int, assignment_type: AssignmentType,
                         scheduled_date: date, location: str,
                         assigned_employee_id: int = None, time_start=None, time_end=None,
                         notes: str = "") -> Assignment:
        """Create a new assignment."""
        session = get_db_session()
        try:
            assignment = Assignment(
                quotation_id=quotation_id,
                type=assignment_type,
                scheduled_date=scheduled_date,
                time_start=time_start,
                time_end=time_end,
                location=location,
                assigned_employee_id=assigned_employee_id,
                notes=notes
            )
            session.add(assignment)
            session.commit()
            session.refresh(assignment)
            return assignment
        finally:
            session.close()
    
    @staticmethod
    def get_assignments_filtered(date_from: date = None, date_to: date = None,
                               assignment_type: AssignmentType = None,
                               employee_id: int = None,
                               status: AssignmentStatus = None) -> List[Assignment]:
        """Get assignments with filters."""
        session = get_db_session()
        try:
            query = (
                session.query(Assignment)
                .options(
                    joinedload(Assignment.quotation).joinedload(Quotation.customer),
                    joinedload(Assignment.assigned_employee)
                )
            )
            
            filters = []
            
            if date_from:
                filters.append(Assignment.scheduled_date >= date_from)
            
            if date_to:
                filters.append(Assignment.scheduled_date <= date_to)
            
            if assignment_type:
                filters.append(Assignment.type == assignment_type)
            
            if employee_id:
                filters.append(Assignment.assigned_employee_id == employee_id)
            
            if status:
                filters.append(Assignment.status == status)
            
            if filters:
                query = query.filter(and_(*filters))
            
            return query.order_by(Assignment.scheduled_date, Assignment.time_start).all()
        finally:
            session.close()
    
    @staticmethod
    def get_all_assignments() -> List[Assignment]:
        """Get all assignments."""
        session = get_db_session()
        try:
            return (
                session.query(Assignment)
                .options(
                    joinedload(Assignment.quotation).joinedload(Quotation.customer),
                    joinedload(Assignment.assigned_employee)
                )
                .order_by(Assignment.scheduled_date.desc(), Assignment.time_start)
                .all()
            )
        finally:
            session.close()
    
    @staticmethod
    def update_assignment_status(assignment_id: int, status: str) -> bool:
        """Update assignment status."""
        session = get_db_session()
        try:
            assignment = session.query(Assignment).filter(Assignment.id == assignment_id).first()
            if not assignment:
                return False
            
            # Map string to enum
            status_map = {
                "planned": AssignmentStatus.PLANNED,
                "in_progress": AssignmentStatus.IN_PROGRESS,
                "done": AssignmentStatus.DONE,
                "cancelled": AssignmentStatus.CANCELLED
            }
            
            if status in status_map:
                assignment.status = status_map[status]
                session.commit()
                return True
            
            return False
        finally:
            session.close()
    
    @staticmethod
    def delete_assignment(assignment_id: int) -> bool:
        """Delete an assignment."""
        session = get_db_session()
        try:
            assignment = session.query(Assignment).filter(Assignment.id == assignment_id).first()
            if not assignment:
                return False
            
            session.delete(assignment)
            session.commit()
            return True
        finally:
            session.close()


class CompanyService:
    """Service for company settings."""
    
    @staticmethod
    def get_company_settings() -> CompanySettings:
        """Get company settings, creating default if none exist."""
        session = get_db_session()
        try:
            settings = session.query(CompanySettings).first()
            if not settings:
                settings = CompanySettings()
                session.add(settings)
                session.commit()
                session.refresh(settings)
            return settings
        finally:
            session.close()
    
    @staticmethod
    def update_company_settings(**kwargs) -> CompanySettings:
        """Update company settings."""
        session = get_db_session()
        try:
            settings = session.query(CompanySettings).first()
            if not settings:
                settings = CompanySettings()
                session.add(settings)
            
            for key, value in kwargs.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
            
            session.commit()
            session.refresh(settings)
            return settings
        finally:
            session.close()
