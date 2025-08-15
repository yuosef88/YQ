"""
Serial number generation for quotations.
Implements Q-YYYY-000001 format with yearly incrementing.
"""

from datetime import datetime
from sqlalchemy import func
from core.database import get_db_session
from core.models import Quotation


def generate_quotation_serial(year: int = None) -> str:
    """
    Generate the next quotation serial number for the given year.
    Format: Q-YYYY-000001
    
    Args:
        year: Year for the serial (defaults to current year)
        
    Returns:
        Next available serial number string
    """
    if year is None:
        year = datetime.now().year
    
    session = get_db_session()
    try:
        # Find the highest serial number for this year
        year_prefix = f"Q-{year}-"
        
        # Query for serials starting with this year's prefix
        latest_serial = (
            session.query(Quotation.serial_number)
            .filter(Quotation.serial_number.like(f"{year_prefix}%"))
            .order_by(Quotation.serial_number.desc())
            .first()
        )
        
        if latest_serial:
            # Extract the number part and increment
            serial_parts = latest_serial[0].split('-')
            if len(serial_parts) == 3:
                try:
                    last_number = int(serial_parts[2])
                    next_number = last_number + 1
                except (ValueError, IndexError):
                    next_number = 1
            else:
                next_number = 1
        else:
            # No serials for this year yet
            next_number = 1
        
        # Format with zero padding to 6 digits
        return f"Q-{year}-{next_number:06d}"
        
    finally:
        session.close()


def is_serial_unique(serial: str) -> bool:
    """
    Check if a serial number is unique in the database.
    
    Args:
        serial: Serial number to check
        
    Returns:
        True if serial is unique, False if already exists
    """
    session = get_db_session()
    try:
        existing = session.query(Quotation).filter(Quotation.serial_number == serial).first()
        return existing is None
    finally:
        session.close()


def validate_serial_format(serial: str) -> bool:
    """
    Validate that a serial number matches the expected format.
    
    Args:
        serial: Serial number to validate
        
    Returns:
        True if format is valid (Q-YYYY-NNNNNN)
    """
    if not serial:
        return False
    
    parts = serial.split('-')
    if len(parts) != 3:
        return False
    
    # Check prefix
    if parts[0] != 'Q':
        return False
    
    # Check year (4 digits)
    try:
        year = int(parts[1])
        if year < 2000 or year > 9999:
            return False
    except ValueError:
        return False
    
    # Check number (6 digits)
    try:
        number = int(parts[2])
        if number < 1 or number > 999999:
            return False
        # Check that it's actually 6 digits (with leading zeros)
        if parts[2] != f"{number:06d}":
            return False
    except ValueError:
        return False
    
    return True
