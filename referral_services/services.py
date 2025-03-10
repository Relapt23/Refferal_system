import base64
import os
import uuid

import requests
from pydantic import EmailStr

HUNTER_API_KEY = os.getenv("HUNTER_API_KEY")


def generate_referral_code():
    uid = uuid.uuid4()
    code = base64.urlsafe_b64encode(uid.bytes).decode("utf-8")[:10]

    return code.upper()


async def get_hunter_info(email: EmailStr) -> dict:
    url = f"https://api.hunter.io/v2/email-verifier?email={email}&api_key={HUNTER_API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json().get("data", {})
    return {}
