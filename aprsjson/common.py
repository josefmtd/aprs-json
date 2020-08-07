import re
from datetime import datetime
from aprsjson import base91
from aprsjson.exceptions import ParseError

__all__ = [
    'parse_timestamp',
    'parse_comment',
    '_parse_data_extensions',
    '_parse_comment_altitude',
    '_parse_dao',
    'parse_status',
    'parse_user_defined',
]

def parse_user_defined(body):
    return ('', {
        'format': 'user-defined',
        'id': body[0],
        'type': body[1],
        'body': body[2:],
        })

def parse_status(packet_type, body):
    body, result = parse_timestamp(body, packet_type)

    result.update({
        'format': 'status',
        'status': body.strip(' ')
        })

    return (body, result)


def parse_timestamp(body, packet_type):
    parsed = {}

    match = re.findall(r"^(\d{6})(.)$", body[0:7])
    if match:
        ts, form = match[0]
        utc = datetime.utcnow()

        timestamp = 0

        if packet_type == '>' and form != 'z':
            pass
        else:
            body = body[7:]

            try:
                # zulu hhmmss format
                if form == 'h':
                    timestamp = "%d%02d%02d%s" % (utc.year, utc.month, utc.day, ts)
                # zulu ddhhmm format
                # '/' local ddhhmm format
                elif form in 'z/':
                    timestamp = "%d%02d%s%02d" % (utc.year, utc.month, ts, 0)
                else:
                    timestamp = "19700101000000"

                td = utc.strptime(timestamp, "%Y%m%d%H%M%S") - datetime(1970, 1, 1)
                timestamp = int((td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6)

            except Exception as exp:
                timestamp = 0
                logger.debug(exp)

        parsed.update({
            'timestamp': int(timestamp),
        })

    return (body, parsed)

def parse_comment(body, parsed):
    body, result = _parse_data_extensions(body)
    parsed.update(result)

    body, result = _parse_comment_altitude(body)
    parsed.update(result)

    body, result = _parse_comment_telemetry(body)
    parsed.update(result)

    body = _parse_dao(body, parsed)

def _parse_data_extensions(body):
    parsed = {}
    match = re.findall(r"^([0-9 .]{3})/([0-9 .]{3})", body)

    if match:
        cse, spd = match[0]
        body = body[7:]
        parsed.update({'course': int(cse) if cse.isdigit() and 1 <= int(cse) <= 360 else 0})
        if spd.isdigit():
            parsed.update({'speed': int(spd)*1.852})

        match = re.findall(r"^/([0-9 .]{3})/([0-9 .]{3})", body)
        if match:
            brg, nrq = match[0]
            body = body[8:]
            if brg.isdigit():
                parsed.update({'bearing': int(brg)})
            if nrq.isdigit():
                parsed.update({'nrq': int(nrq)})
    else:
        match = re.findall(r"^(PHG(\d[\x30-\x7e]\d\d[0-9A-Z]?))", body)
        if match:
            ext, phg = match[0]
            body = body[len(ext):]
            parsed.update({'phg': phg})
        else:
            match = re.findall(r"^RNG(\d{4})", body)
            if match:
                rng = match[0]
                body = body[7:]
                parsed.update({'rng': int(rng) * 1.609344})  # miles to km

    return body, parsed

def _parse_comment_altitude(body):
    parsed = {}
    match = re.findall(r"^(.*?)/A=(\-\d{5}|\d{6})(.*)$", body)
    if match:
        body, altitude, rest = match[0]
        body += rest
        parsed.update({'altitude': int(altitude)*0.3048})

    return body, parsed

def _parse_dao(body, parsed):
    match = re.findall("^(.*)\!([\x21-\x7b])([\x20-\x7b]{2})\!(.*?)$", body)
    if match:
        body, daobyte, dao, rest = match[0]
        body += rest

        parsed.update({'daodatumbyte': daobyte.upper()})
        lat_offset = lon_offset = 0

        if daobyte == 'W' and dao.isdigit():
            lat_offset = int(dao[0]) * 0.001 / 60
            lon_offset = int(dao[1]) * 0.001 / 60
        elif daobyte == 'w' and ' ' not in dao:
            lat_offset = (base91.to_decimal(dao[0]) / 91.0) * 0.01 / 60
            lon_offset = (base91.to_decimal(dao[1]) / 91.0) * 0.01 / 60

        parsed['latitude'] += lat_offset if parsed['latitude'] >= 0 else -lat_offset
        parsed['longitude'] += lon_offset if parsed['longitude'] >= 0 else -lon_offset

    return body

def _parse_comment_telemetry(body):
    """
    Looks for base91 telemetry found in comment field
    Returns [remaining_text, telemetry]
    """
    parsed = {}
    match = re.findall(r"^(.*?)\|([!-{]{4,14})\|(.*)$", body)

    if match and len(match[0][1]) % 2 == 0:
        body, telemetry, post = match[0]
        body += post

        temp = [0] * 7
        for i in range(7):
            temp[i] = base91.to_decimal(telemetry[i*2:i*2+2])

        parsed.update({
            'telemetry': {
                'seq': temp[0],
                'vals': temp[1:6]
                }
            })

        if temp[6] != '':
            parsed['telemetry'].update({
                'bits': "{0:08b}".format(temp[6] & 0xFF)[::-1]
                })

    return (body, parsed)
