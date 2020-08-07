import aprs

"""
Exception definitions for APRS JSON Module
"""

__all__ = [
    "GenericError",
    "UnknownFormat",
    "ParsingError",
]

class GenericError(Exception):
    """
    Base exception class
    """
    def __init__(self, message):
        super(GenericError, self).__init__(message)
        self.message = message

class UnknownFormat(GenericError):
    """
    Raised when aprsjson.parse() finds an unsupported packet format
    """

    def __init__(self, message, frame = aprs.Frame):
        super(UnknownFormat, self).__init__(message)
        self.frame = frame

class ParseError(GenericError):
    """
    Raised when aprsjson.parse() unable to parse a supported packet format
    """
    def __init__(self, message, frame = aprs.Frame):
        super(ParseError, self).__init__(message)
        self.frame = frame
