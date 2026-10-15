"""Security tests verifying SSRF protection rules."""

from __future__ import annotations

import pytest
from ssrf import SSRFSecurityError, validate_url_against_ssrf


@pytest.mark.parametrize(
    "blocked_url",
    [
        "http://127.0.0.1",
        "http://127.0.0.1:8080/admin",
        "http://localhost",
        "http://localhost:3000",
        "http://[::1]",
        "http://0.0.0.0",
        # Cloud metadata service (AWS, GCP, Azure, OpenStack)
        "http://169.254.169.254",
        "http://169.254.169.254/latest/meta-data/",
        "http://169.254.0.1",
        # RFC 1918 Private networks
        "http://10.0.0.1",
        "http://10.254.254.254",
        "http://172.16.0.1",
        "http://172.31.255.255",
        "http://192.168.0.1",
        "http://192.168.1.100",
        # Carrier-grade NAT
        "http://100.64.0.1",
        # Documentation / benchmark ranges
        "http://192.0.2.1",
        "http://198.51.100.1",
        "http://203.0.113.1",
        # Non-HTTP schemes
        "file:///etc/passwd",
        "ftp://example.com/file",
        "gopher://127.0.0.1:70",
        # Embedded credentials
        "http://admin:secret@example.com",
    ],
)
def test_ssrf_blocks_private_and_malicious_urls(blocked_url: str) -> None:
    """SSRF validator strictly blocks loopback, private IP, metadata, and invalid schemes."""
    with pytest.raises(SSRFSecurityError):
        validate_url_against_ssrf(blocked_url)


def test_ssrf_rejects_empty_or_malformed_url() -> None:
    """Empty or non-string URLs are rejected."""
    with pytest.raises(SSRFSecurityError):
        validate_url_against_ssrf("")

    with pytest.raises(SSRFSecurityError):
        validate_url_against_ssrf("not-a-valid-url")


def test_ssrf_allows_public_ip_and_domain() -> None:
    """Public domain URLs pass SSRF verification."""
    # 8.8.8.8 is a public DNS IP literal
    validate_url_against_ssrf("https://8.8.8.8")
    # example.com resolves to public IANA IP (93.184.215.14)
    validate_url_against_ssrf("https://example.com")
