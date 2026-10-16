"""Cryptographic utilities for authenticated encryption at rest using AES-256-GCM."""

from __future__ import annotations

import base64
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from shared.config import get_settings

KEY_SALT = b"varistha-secrets-v1"
CIPHER_PREFIX = "v1:"


class CryptoError(Exception):
    """Base exception for cryptographic operations."""


class DecryptionError(CryptoError):
    """Raised when ciphertext cannot be decrypted or authentication tag is invalid."""


def derive_key(secret_material: str, salt: bytes = KEY_SALT) -> bytes:
    """Derive a 256-bit symmetric key from secret material using HKDF-SHA256."""
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        info=b"varistha-master-key",
    )
    return hkdf.derive(secret_material.encode("utf-8"))


def get_master_encryption_key() -> bytes:
    """Retrieve or derive the 256-bit AES-GCM master key."""
    settings = get_settings()
    if settings.encryption_key:
        try:
            decoded = base64.b64decode(settings.encryption_key.strip())
            if len(decoded) == 32:
                return decoded
        except (ValueError, TypeError):
            pass
    return derive_key(settings.secret_key)


def encrypt_secret(plaintext: str, associated_data: bytes | None = None) -> str:
    """Encrypt plaintext string using AES-256-GCM.

    Returns string formatted as 'v1:<base64(12-byte nonce + ciphertext + 16-byte tag)>'.
    """
    master_key = get_master_encryption_key()
    aesgcm = AESGCM(master_key)
    nonce = os.urandom(12)  # 96-bit unique nonce per encryption

    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), associated_data)
    payload = nonce + ciphertext
    encoded = base64.b64encode(payload).decode("ascii")
    return f"{CIPHER_PREFIX}{encoded}"


def decrypt_secret(encrypted_text: str, associated_data: bytes | None = None) -> str:
    """Decrypt authenticated AES-256-GCM ciphertext.

    Raises DecryptionError if prefix is invalid or message was tampered with.
    """
    if not encrypted_text.startswith(CIPHER_PREFIX):
        raise DecryptionError("Invalid or unsupported ciphertext format.")

    encoded_payload = encrypted_text[len(CIPHER_PREFIX) :]
    try:
        payload = base64.b64decode(encoded_payload)
    except Exception as exc:
        raise DecryptionError(f"Malformed base64 ciphertext: {exc}") from exc

    if len(payload) < 28:  # 12-byte nonce + 16-byte tag minimum
        raise DecryptionError("Ciphertext payload is shorter than minimum required length.")

    nonce = payload[:12]
    ciphertext_with_tag = payload[12:]
    master_key = get_master_encryption_key()
    aesgcm = AESGCM(master_key)

    try:
        decrypted_bytes = aesgcm.decrypt(nonce, ciphertext_with_tag, associated_data)
        return decrypted_bytes.decode("utf-8")
    except InvalidTag as exc:
        msg = "Authentication tag verification failed; ciphertext tampered."
        raise DecryptionError(msg) from exc
    except Exception as exc:
        raise DecryptionError(f"Decryption failed: {exc}") from exc
