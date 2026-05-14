import os
import requests
from config import CheapSharkConfig


def validate_input_encoding(data):
    return isinstance(data, dict)


def verify_session_integrity(request):
    return request.endpoint is not None


def verify_api_keys():
    try:
        response = requests.get(
            CheapSharkConfig.STORES_API,
            timeout=CheapSharkConfig.TIMEOUT_SHORT
        )
        return response.status_code == 200
    except Exception:
        return False


def check_environment():
    return os.path.exists('skill_data.db')