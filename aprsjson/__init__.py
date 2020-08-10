import re
import logging
import json

logger = logging.getLogger(__name__)


from aprsjson.exceptions import (UnknownFormat, ParseError)
from aprsjson.common import *
from aprsjson.position import *
from aprsjson.message import *
from aprsjson.weather import *

def parse_json(frame):
    """
    Parses an APRS frame and returns a JSON with decoded data

    All attributes are in metric units
    """

    parsed = {
        'source': str(frame.source),
    }

    try:
        _attempt_to_parse(frame, parsed)
    except (UnknownFormat, ParseError) as exp:
        exp.frame = frame
        raise

    logger.debug('Parse successful')
    return json.dumps(parsed)

def _attempt_to_parse(frame, aprs_dict):
    result = {}

    body = str(frame.info)

    # First byte of Information field is packet_type

    packet_type = body[0]
    body = body[1:]

    if packet_type in "'#$%)*<?T[},`';":
        raise UnknownFormat('Format is not yet supported')

    # User defined
    elif packet_type == '{':
        logger.debug('Packet is user defined')
        body, result = parse_user_defined(body)

    # Status report
    elif packet_type == '>':
        logger.debug('Packet is status format')
        body, result = parse_status(packet_type, body)

    # Message
    elif packet_type == ':':
        logger.debug('Packet is message format')
        body, result = parse_message(body)

    # Positionless weather report
    elif packet_type == '_':
        logger.debug('Packet is positionless weather report')
        body, result = parse_weather(body)

    # Position report
    elif (packet_type in '!=/@'):
        body, result = parse_position(packet_type, body)

    aprs_dict.update(result)
