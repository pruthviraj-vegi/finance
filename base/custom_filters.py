"""
Custom template filters for formatting currency, dates, and other utilities.
"""

import base64
import locale
import logging
import re

from django import template
from num2words import num2words

logger = logging.getLogger(__name__)

locale.setlocale(locale.LC_ALL, "en_IN")

register = template.Library()

formate = {
    "grouping": True,  # Enable thousands grouping
    "grouping_threshold": 3,  # Group digits in threes
    "decimal_point": ".",  # Use dot as the decimal separator
    "frac_digits": 2,  # Show 2 digits after the decimal point
}


_CURRENCY_SYMBOLS = str.maketrans("", "", "₹$€£,")


def _convert_to_numeric(value):
    """
    Bulletproof string-to-number converter that handles various input formats.

    Args:
        value: String, int, float, or other value to convert

    Returns:
        float or int: Converted numeric value, or None if conversion fails
    """
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return value

    cleaned = str(value).strip().translate(_CURRENCY_SYMBOLS)

    if not cleaned:
        return None

    # Extract sign and percentage flags via regex
    match = re.fullmatch(r"(-?)(\d+(?:\.\d+)?)(%%?)?", cleaned)
    if not match:
        logger.warning("Failed to convert '%s' to numeric", value)
        return None

    is_negative = bool(match.group(1))
    is_percentage = bool(match.group(3))

    try:
        numeric_value = float(match.group(2))

        if is_percentage:
            numeric_value /= 100
        if is_negative:
            numeric_value = -numeric_value

        if numeric_value.is_integer() and abs(numeric_value) < 1e15:
            return int(numeric_value)

        return numeric_value

    except (ValueError, OverflowError) as e:
        logger.warning("Failed to convert '%s' to numeric: %s", value, e)
        return None


@register.filter(name="currency")
def currency(value, _arg=None):
    """
    Bulletproof currency formatter that handles strings, integers, floats, and None values.
    Converts string inputs to appropriate numeric types before formatting.
    """
    try:
        if value is None or value == "":
            return "0.00"

        # Convert string to number if needed
        numeric_value = _convert_to_numeric(value)

        if numeric_value is None:
            logger.warning("Could not convert value '%s' to numeric format", value)
            return "0.00"

        data = locale.format_string(
            f"%.{formate['frac_digits']}f",
            numeric_value,
            grouping=formate["grouping"],
            monetary=False,
        )
        return data
    except (TypeError, ValueError, locale.Error) as e:
        logger.error("Currency formatting error for value '%s': %s", value, e)
        return "0.00"


@register.filter(name="currency_nonDecimal")
def currency_non_decimal(value, _arg=None):
    """
    Bulletproof non-decimal currency formatter for integer values.
    """
    try:
        if value is None or value == "":
            return "0"

        # Convert string to number if needed
        numeric_value = _convert_to_numeric(value)

        if numeric_value is None:
            logger.warning("Could not convert value '%s' to numeric format", value)
            return "0"

        # Convert to integer
        value_int = int(numeric_value)

        return locale.format_string(
            "%d",
            value_int,
            grouping=formate["grouping"],
            monetary=False,
        )
    except (TypeError, ValueError, locale.Error) as e:
        logger.error(
            "Currency non-decimal formatting error for value '%s': %s", value, e
        )
        return "0"


@register.filter(name="currency_abbreviation")
def currency_abbreviation(value):
    """
    Bulletproof currency abbreviation formatter that handles strings and various input formats.

    Examples:
    1000 -> 1k
    100000 -> 100,000.00 (or localized equivalent)
    1234567 -> 1.23M
    """
    try:
        if value is None or value == "":
            return "0.00"

        # Convert string to number if needed
        numeric_value = _convert_to_numeric(value)

        if numeric_value is None:
            logger.warning("Could not convert value '%s' to numeric format", value)
            return "0.00"

        # Check for 'k', 'M', 'B' abbreviations
        if numeric_value >= 1_000_000_000:
            return f"{numeric_value / 1_000_000_000:.2f}B"
        elif numeric_value >= 1_000_000:
            return f"{numeric_value / 1_000_000:.2f}M"
        elif numeric_value >= 1000:
            return f"{numeric_value / 1000:.1f}k"

        # Set locale for international formatting (e.g., thousands separators)
        try:
            locale.setlocale(locale.LC_ALL, "")
        except locale.Error:
            # Fallback if the system's default locale isn't set
            locale.setlocale(locale.LC_ALL, "en_US.UTF-8")

        # Use locale.format_string for international formatting
        return locale.format_string("%.2f", numeric_value, grouping=True)

    except (TypeError, ValueError, locale.Error) as e:
        logger.error(
            "Currency abbreviation formatting error for value '%s': %s", value, e
        )
        return "0.00"


@register.filter(name="currencyToWord")
def currency_to_word(value, _arg=None):
    """Convert currency value to Indian Rupess text format."""
    try:
        amount = float(value)
        return num2words(amount, lang="en_IN", to="currency", currency="INR").title()
    except (ValueError, TypeError) as e:
        logger.error("Currency to word formatting error for value '%s': %s", value, e)
        return value


@register.filter(name="phone_number")
def phone_number(value):
    """Format a 10-digit phone number with a space in the middle."""
    if value is None:
        return ""
    try:
        numbers = value.replace(" ", "")
        return f"{numbers[:5]} {numbers[5:]}" if len(numbers) == 10 else numbers
    except (TypeError, ValueError) as e:
        logger.error(e)
        return value


@register.filter(name="b64encode")
def base64_encode(value):
    """Encode a string or bytes using base64 and return a UTF-8 string."""
    return base64.b64encode(value).decode("utf-8")
