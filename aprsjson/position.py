import logging
import re

from aprsjson import base91, logger
from aprsjson.exceptions import ParseError
from aprsjson.common import parse_timestamp, parse_comment
from aprsjson.weather import parse_weather_data

__all__ = [
        'parse_position',
        'parse_compressed',
        'parse_normal',
        ]

def parse_position(packet_type, body):
    parsed = {}
    # decode timestamp
    if packet_type in "/@;":
        body, result = parse_timestamp(body, packet_type)
        parsed.update(result)

    if len(body) == 0 and 'timestamp' in parsed:
        raise ParseError("invalid position report format")

    # decode body
    body, result = parse_compressed(body)
    parsed.update(result)

    if len(result) > 0:
        logger.debug("Parsed as compressed position report")
    else:
        body, result = parse_normal(body)
        parsed.update(result)

        if len(result) > 0:
            logger.debug("Parsed as normal position report")
        else:
            raise ParseError("invalid position format")
    # check comment for weather information
    # Page 62 of the spec
    if parsed['symbol'][1] == '_':
        logger.debug("Attempting to parse weather report from comment")
        body, result = parse_weather_data(body)
        parsed.update({
            'comment': body.strip(' '),
            'weather': result,
            })
    else:
        # decode comment
        parse_comment(body, parsed)
    
    return ('', parsed)

def parse_compressed(body):
    parsed = {}

    if re.match(r"^[\/\\A-Za-j][!-|]{8}[!-{}][ -|]{3}", body):
        logger.debug("Attempting to parse as compressed position report")

        if len(body) < 13:
            raise ParseError("Invalid compressed packet (less than 13 characters)")

        compressed = body[:13]
        body = body[13:]

        symbol_table = compressed[0]
        symbol = compressed[9]

        try:
            latitude = 90 - (base91.to_decimal(compressed[1:5]) / 380926.0)
            longitude = -180 + (base91.to_decimal(compressed[5:9]) / 190463.0)
        except ValueError:
            raise ParseError("invalid characters in latitude/longitude encoding")

        # parse csT

        # converts the relevant characters from base91
        c1, s1, ctype = [ord(x) - 33 for x in compressed[10:13]]

        # if c1 == -1:
        #     parsed.update({'gpsfixstatus': 1 if ctype & 0x20 == 0x20 else 0})

        if -1 in [c1, s1]:
            pass
        elif ctype & 0x18 == 0x10:
            parsed.update({'altitude': (1.002 ** (c1 * 91 + s1)) * 0.3048})
        elif c1 >= 0 and c1 <= 89:
            parsed.update({'course': 360 if c1 == 0 else c1 * 4})
            parsed.update({'speed': (1.08 ** s1 - 1) * 1.852})  # mul = convert knts to kmh
        elif c1 == 90:
            parsed.update({'radiorange': (2 * 1.08 ** s1) * 1.609344})  # mul = convert mph to kmh

        parsed.update({
            'symbol': symbol_table + symbol,
            'latitude': latitude,
            'longitude': longitude,
            })

    return (body, parsed)


def parse_normal(body):
    parsed = {}
    match = re.findall(r"^(\d{2})([0-9 ]{2}\.[0-9 ]{2})([NnSs])([\/\\0-9A-Z])(\d{3})([0-9 ]{2}\.[0-9 ]{2})([EeWw])([\x21-\x7e])(.*)$", body)

    if match:
        (
            lat_deg,
            lat_min,
            lat_dir,
            symbol_table,
            lon_deg,
            lon_min,
            lon_dir,
            symbol,
            body
        ) = match[0]

        # position ambiguity
        posambiguity = lat_min.count(' ')

        if posambiguity != lon_min.count(' '):
            raise ParseError("latitude and longitude ambiguity mismatch")

        # parsed.update({'posambiguity': posambiguity})

        # we center the position inside the ambiguity box
        if posambiguity >= 4:
            lat_min = "30"
            lon_min = "30"
        else:
            lat_min = lat_min.replace(' ', '5', 1)
            lon_min = lon_min.replace(' ', '5', 1)

        # validate longitude and latitude

        if int(lat_deg) > 89 or int(lat_deg) < 0:
            raise ParseError("latitude is out of range (0-90 degrees)")
        if int(lon_deg) > 179 or int(lon_deg) < 0:
            raise ParseError("longitude is out of range (0-180 degrees)")
        """
        f float(lat_min) >= 60:
            raise ParseError("latitude minutes are out of range (0-60)")
        if float(lon_min) >= 60:
            raise ParseError("longitude minutes are out of range (0-60)")
        The above is commented out intentionally
        apparently aprs.fi doesn't bound check minutes
        and there are actual packets that have >60min
        i don't even know why that's the case
        """

        # convert coordinates from DDMM.MM to decimal
        latitude = int(lat_deg) + (float(lat_min) / 60.0)
        longitude = int(lon_deg) + (float(lon_min) / 60.0)

        latitude *= -1 if lat_dir in 'Ss' else 1
        longitude *= -1 if lon_dir in 'Ww' else 1

        parsed.update({
            'symbol': symbol_table + symbol,
            'latitude': latitude,
            'longitude': longitude,
            })

    return (body, parsed)
