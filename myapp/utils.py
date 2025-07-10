import hashlib
import urllib.parse
from django.utils.timezone import now

def generate_check_mac_value(params, hash_key, hash_iv):
    sorted_params = sorted(params.items())
    encode_str = f"HashKey={hash_key}&" + \
                 '&'.join(f"{k}={v}" for k, v in sorted_params) + \
                 f"&HashIV={hash_iv}"
    encode_str = urllib.parse.quote_plus(encode_str).lower()
    encode_str = (encode_str.replace('%2d', '-').replace('%5f', '_')
                .replace('%2e', '.').replace('%21', '!')
                .replace('%2a', '*').replace('%28', '(')
                .replace('%29', ')'))
    return hashlib.sha256(encode_str.encode('utf-8')).hexdigest().upper()

