import base64
import hashlib

from cryptography.fernet import Fernet  # pyright: ignore[reportMissingImports]
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def _get_fernet() -> Fernet:
    key_source = getattr(settings, 'AI_PLATFORM_ENCRYPTION_KEY', '').strip()
    if not key_source:
        raise ImproperlyConfigured('AI_PLATFORM_ENCRYPTION_KEY is required.')

    digest = hashlib.sha256(key_source.encode('utf-8')).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_secret(value: str) -> str:
    if not value:
        return ''
    return _get_fernet().encrypt(value.encode('utf-8')).decode('utf-8')


def decrypt_secret(value: str) -> str:
    if not value:
        return ''
    return _get_fernet().decrypt(value.encode('utf-8')).decode('utf-8')


def mask_secret(value: str) -> str:
    if not value:
        return ''
    visible = 4
    if len(value) <= visible:
        return '*' * len(value)
    return f"{'*' * (len(value) - visible)}{value[-visible:]}"
