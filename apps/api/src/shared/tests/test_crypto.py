"""Tests for authenticated AES-256-GCM encryption at rest."""

from __future__ import annotations

import base64

import pytest
from shared.crypto import (
    CIPHER_PREFIX,
    DecryptionError,
    decrypt_secret,
    derive_key,
    encrypt_secret,
)


def test_derive_key_deterministic() -> None:
    """HKDF key derivation produces 32-byte key deterministically."""
    k1 = derive_key("my-secret-key")
    k2 = derive_key("my-secret-key")
    k3 = derive_key("another-secret-key")

    assert len(k1) == 32
    assert k1 == k2
    assert k1 != k3


def test_encrypt_decrypt_roundtrip() -> None:
    """Plaintext is preserved exactly across encryption and decryption."""
    secret = "sk-live-0123456789abcdef-super-secret-token"  # noqa: S105
    encrypted = encrypt_secret(secret)

    assert encrypted.startswith(CIPHER_PREFIX)
    assert encrypted != secret
    assert secret not in encrypted

    decrypted = decrypt_secret(encrypted)
    assert decrypted == secret


def test_nonce_randomness_each_run() -> None:
    """Encrypting the same plaintext twice produces different ciphertexts."""
    secret = "same-plaintext"  # noqa: S105
    enc1 = encrypt_secret(secret)
    enc2 = encrypt_secret(secret)

    assert enc1 != enc2
    assert decrypt_secret(enc1) == secret
    assert decrypt_secret(enc2) == secret


def test_tampered_ciphertext_rejected() -> None:
    """Modifying even 1 byte in the ciphertext payload raises DecryptionError."""
    secret = "secret-payload-to-protect"  # noqa: S105
    encrypted = encrypt_secret(secret)

    # Decode and tamper payload
    encoded = encrypted[len(CIPHER_PREFIX) :]
    raw = bytearray(base64.b64decode(encoded))
    # Flip one bit in ciphertext
    raw[-1] ^= 0x01
    tampered = f"{CIPHER_PREFIX}{base64.b64encode(raw).decode('ascii')}"

    with pytest.raises(DecryptionError, match="Authentication tag verification failed"):
        decrypt_secret(tampered)


def test_invalid_prefix_or_malformed_rejected() -> None:
    """Invalid prefixes or invalid payloads raise DecryptionError."""
    with pytest.raises(DecryptionError, match="Invalid or unsupported ciphertext format"):
        decrypt_secret("not-encrypted")

    with pytest.raises(DecryptionError, match="Invalid or unsupported ciphertext format"):
        decrypt_secret("v2:something")

    with pytest.raises(DecryptionError, match="Malformed base64 ciphertext"):
        decrypt_secret(f"{CIPHER_PREFIX}!!!invalid_base64!!!")

    short_b64 = base64.b64encode(b"short").decode("ascii")
    with pytest.raises(DecryptionError, match="shorter than minimum required length"):
        decrypt_secret(f"{CIPHER_PREFIX}{short_b64}")


def test_associated_data_protection() -> None:
    """Ciphertexts encrypted with associated data require identical AD to decrypt."""
    secret = "tenant-specific-secret"  # noqa: S105
    ad = b"tenant-id-42"
    encrypted = encrypt_secret(secret, associated_data=ad)

    # Correct AD decrypts
    assert decrypt_secret(encrypted, associated_data=ad) == secret

    # Wrong AD fails authentication
    with pytest.raises(DecryptionError):
        decrypt_secret(encrypted, associated_data=b"tenant-id-99")
