"""Password hashing (scrypt) and signed session tokens, standard library only."""
import base64
import hashlib
import hmac
import os
import time

from appdb import DATA_DIR


def hash_password(pw: str) -> str:
    salt = os.urandom(16)
    h = hashlib.scrypt(pw.encode(), salt=salt, n=2 ** 14, r=8, p=1, dklen=32)
    return f"scrypt${salt.hex()}${h.hex()}"


def verify_password(pw: str, stored: str) -> bool:
    try:
        _, salt, h = stored.split("$")
        calc = hashlib.scrypt(pw.encode(), salt=bytes.fromhex(salt), n=2 ** 14, r=8, p=1, dklen=32)
        return hmac.compare_digest(calc.hex(), h)
    except Exception:
        return False


DUMMY_HASH = hash_password("dummy-password-for-timing")


def _secret() -> bytes:
    env = os.environ.get("APP_SECRET")
    if env:
        return env.encode()
    path = os.path.join(DATA_DIR, ".secret")
    if not os.path.exists(path):
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(path, "wb") as f:
            f.write(base64.urlsafe_b64encode(os.urandom(32)))
    with open(path, "rb") as f:
        return f.read()


SECRET = _secret()
TTL = 8 * 3600


def make_token(patient_id: int) -> str:
    body = base64.urlsafe_b64encode(f"{patient_id}.{int(time.time()) + TTL}".encode()).decode()
    sig = hmac.new(SECRET, body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def read_token(token):
    try:
        body, sig = (token or "").rsplit(".", 1)
        good = hmac.new(SECRET, body.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, good):
            return None
        pid, exp = base64.urlsafe_b64decode(body.encode()).decode().split(".")
        return int(pid) if int(exp) > time.time() else None
    except Exception:
        return None
