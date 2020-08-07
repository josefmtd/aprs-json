import re
from aprsjson import logger

def parse_message(body):
    parsed = {}

    # the while loop is used to easily break out once a match is found
    while True:
        # try to match bulletin
        match = re.findall(r"^BLN([0-9])([a-z0-9_ \-]{5}):(.{0,67})", body, re.I)
        if match:
            bid, identifier, text = match[0]
            identifier = identifier.rstrip(' ')

            mformat = 'bulletin' if identifier == "" else 'group-bulletin'

            parsed.update({
                'format': mformat,
                'message_text': text.strip(' '),
                'bid': bid,
                'identifier': identifier
                })
            break

        # try to match announcement
        match = re.findall(r"^BLN([A-Z])([a-zA-Z0-9_ \-]{5}):(.{0,67})", body)
        if match:
            aid, identifier, text = match[0]
            identifier = identifier.rstrip(' ')

            parsed.update({
                'format': 'announcement',
                'message_text': text.strip(' '),
                'aid': aid,
                'identifier': identifier
                })
            break

        # validate addresse
        match = re.findall(r"^([a-zA-Z0-9_ \-]{9}):(.*)$", body)
        if not match:
            break

        addresse, body = match[0]

        parsed.update({'addresse': addresse.rstrip(' ')})


        parsed.update({'format': 'message'})

        match = re.search(r"^(ack|rej)([A-Za-z0-9]{1,5})$", body)
        if match:
            parsed.update({
                'response': match.group(1),
                'msgNo': match.group(2),
                })
        else:
            body = body[0:70]

            match = re.search(r"{([A-Za-z0-9]{1,5})$", body)
            if match:
                msgNo = match.group(1)
                body = body[:len(body) - 1 - len(msgNo)]

                parsed.update({'msgNo': msgNo})

            parsed.update({'message_text': body.strip(' ')})

        break

    return ('', parsed)
