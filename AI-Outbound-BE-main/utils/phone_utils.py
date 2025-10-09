import re
import logging

# Configure logging
logger = logging.getLogger(__name__)

def format_phone_number(phone_number: str) -> str:
    """
    Format phone number by adding '+' prefix if not present.
    Removes any spaces, dashes, or parentheses before adding '+'.
    
    Args:
        phone_number (str): Raw phone number from CSV
        
    Returns:
        str: Formatted phone number with '+' prefix
    """
    if not phone_number:
        return phone_number
    
    # Remove any spaces, dashes, parentheses, and other non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', phone_number.strip())
    
    # If it doesn't start with +, add it
    if not cleaned.startswith('+'):
        cleaned = '+' + cleaned
    
    return cleaned

def validate_phone_number(phone_number: str) -> bool:
    """
    Validate if a phone number is in a valid format.
    
    Args:
        phone_number (str): Phone number to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not phone_number or phone_number == '+':
        return False
    
    # Check if it starts with + and has at least 10 digits
    if phone_number.startswith('+') and len(phone_number) >= 11:
        # Remove + and check if remaining characters are all digits
        digits_only = phone_number[1:]
        return digits_only.isdigit()
    
    return False

def format_and_validate_phone(phone_number: str) -> tuple[str, bool]:
    """
    Format and validate a phone number.
    
    Args:
        phone_number (str): Raw phone number
        
    Returns:
        tuple: (formatted_phone, is_valid)
    """
    formatted = format_phone_number(phone_number)
    is_valid = validate_phone_number(formatted)
    return formatted, is_valid
