import random
import string
import io

import qrcode

from datetime import datetime, timezone
def unix_time_to_gmt_string(unix_time):
    # Convert the Unix timestamp to a datetime object in GMT
    gmt_time = datetime.fromtimestamp(unix_time, tz=timezone.utc)

    # Format the date and time into a string
    formatted_time = gmt_time.strftime("%Y-%m-%d %H:%M GMT")

    return formatted_time
def generate_id(length=10):
    characters = string.ascii_uppercase + string.digits
    unique_id = ''.join(random.choice(characters) for i in range(length))
    return unique_id


def generate_wallet_address_qr_code(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img_bytes = io.BytesIO()
    img.save(img_bytes)
    img_bytes.seek(0)
    return img_bytes
