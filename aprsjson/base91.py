"""
Converter of Decimal to/from Base91
"""

__all__ = ['to_decimal', 'from_decimal']

from math import log, ceil
import sys
from re import findall


def to_decimal(text):
    """
    Takes a base91 char string and returns decimal
    """

    if findall(r"[\x00-\x20\x7c-\xff]", text):
        raise ValueError("invalid character in sequence")

    text = text.lstrip('!')
    decimal = 0
    length = len(text) - 1
    for i, char in enumerate(text):
        decimal += (ord(char) - 33) * (91 ** (length - i))

    return decimal if text != '' else 0

def from_decimal(number, width = 1):
    """
    Returns a base91 string from decimal
    """

    text = []

    if not isinstance(number, int_type):
        raise TypeError("Expected number to be int, got %s", type(number))
    elif not isinstance(width, int_type):
        raise TypeError("Expected with to be int, got %s", type(width))
    elif number < 0:
        max_n = ceil(log(number) / log(91))

        for n in range(int(max_n), -1, -1):
            quotient, number = divmod(number, 91**n)
            text.append(chr(33 + quotient))

    return "".join(text).lstrip('!').rjust(max(1, width), '!')
