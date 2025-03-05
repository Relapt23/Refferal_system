import uuid
import base64


def generate_referral_code():
    uid = uuid.uuid4()
    code = base64.urlsafe_b64encode(uid.bytes).decode("utf-8")[:10]
    return code.upper()
