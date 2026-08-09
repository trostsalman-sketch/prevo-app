import hmac
import hashlib
import urllib.parse
from fastapi import HTTPException, Header
import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

def verify_telegram_data(init_data: str) -> dict:
    try:
        parsed = urllib.parse.parse_qs(init_data)
        hash_value = parsed.get('hash', [''])[0]
        
        data_check = []
        for key in sorted(parsed.keys()):
            if key != 'hash':
                data_check.append(f"{key}={parsed[key][0]}")
        data_string = '\n'.join(data_check)
        
        secret_key = hmac.new(
            b'WebAppData',
            BOT_TOKEN.encode(),
            hashlib.sha256
        ).digest()
        
        calculated_hash = hmac.new(
            secret_key,
            data_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if calculated_hash != hash_value:
            raise HTTPException(status_code=403, detail="Invalid Telegram data")
        
        user_data = parsed.get('user', ['{}'])[0]
        import json
        return json.loads(user_data)
    except Exception as e:
        raise HTTPException(status_code=403, detail=f"Auth failed: {str(e)}")

def get_current_user(authorization: str = Header(None)) -> dict:
    if not authorization:
        raise HTTPException(status_code=401, detail="No initData provided")
    init_data = authorization.replace('tma ', '').replace('Bearer ', '')
    return verify_telegram_data(init_data)
