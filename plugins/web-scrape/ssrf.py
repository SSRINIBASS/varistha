"""Server-Side Request Forgery (SSRF) protection module for web-scrape."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

# CIDR blocks explicitly forbidden to protect against SSRF and cloud metadata access
BLOCKED_NETWORKS: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = [
    ipaddress.ip_network("0.0.0.0/8"),  # Current network
    ipaddress.ip_network("10.0.0.0/8"),  # Private Class A
    ipaddress.ip_network("100.64.0.0/10"),  # Carrier-grade NAT
    ipaddress.ip_network("127.0.0.0/8"),  # Loopback
    ipaddress.ip_network("169.254.0.0/16"),  # Link-local / Cloud metadata (AWS/GCP/Azure)
    ipaddress.ip_network("172.16.0.0/12"),  # Private Class B
    ipaddress.ip_network("192.0.0.0/24"),  # IETF Protocol Assignments
    ipaddress.ip_network("192.0.2.0/24"),  # TEST-NET-1 documentation
    ipaddress.ip_network("192.168.0.0/16"),  # Private Class C
    ipaddress.ip_network("198.18.0.0/15"),  # Network benchmark testing
    ipaddress.ip_network("198.51.100.0/24"),  # TEST-NET-2 documentation
    ipaddress.ip_network("203.0.113.0/24"),  # TEST-NET-3 documentation
    ipaddress.ip_network("224.0.0.0/4"),  # Multicast
    ipaddress.ip_network("240.0.0.0/4"),  # Reserved for future use
    ipaddress.ip_network("255.255.255.255/32"),  # Broadcast
    # IPv6
    ipaddress.ip_network("::/128"),  # Unspecified
    ipaddress.ip_network("::1/128"),  # Loopback
    ipaddress.ip_network("fc00::/7"),  # Unique Local Address (ULA)
    ipaddress.ip_network("fe80::/10"),  # Link-Local Unicast
    ipaddress.ip_network("ff00::/8"),  # Multicast
]

ALLOWED_SCHEMES = {"http", "https"}


class SSRFSecurityError(Exception):
    """Raised when an outbound URL violates SSRF safety rules."""


def is_ip_blocked(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Return True if the IP address belongs to any blocked or private network."""
    if (
        ip.is_loopback
        or ip.is_private
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    ):
        return True

    return any(ip in network for network in BLOCKED_NETWORKS)


def validate_url_against_ssrf(url: str) -> None:
    """Validate that a URL is safe to fetch and does not resolve to private/internal networks.

    Raises:
        SSRFSecurityError: If the URL uses an unapproved scheme, contains credentials,
                           has no hostname, or resolves to a private/loopback/metadata IP.

    """
    if not url:
        raise SSRFSecurityError("URL must be a non-empty string.")

    parsed = urlparse(url)

    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise SSRFSecurityError(
            f"Scheme '{parsed.scheme}' is not allowed. Only HTTP and HTTPS are permitted."
        )

    if parsed.username or parsed.password:
        raise SSRFSecurityError("URLs containing embedded user credentials are not permitted.")

    hostname = parsed.hostname
    if not hostname:
        raise SSRFSecurityError("URL must have a valid hostname.")

    clean_host = hostname.strip().lower()

    is_local = clean_host in {
        "localhost",
        "localhost.localdomain",
        "broadcasthost",
    } or clean_host.endswith(".local")
    if is_local:
        raise SSRFSecurityError(
            f"Access to local hostname '{clean_host}' is blocked for SSRF defense."
        )

    try:
        ip = ipaddress.ip_address(clean_host)
        if is_ip_blocked(ip):
            raise SSRFSecurityError(
                f"Access to blocked/private IP address '{clean_host}' is prohibited."
            )
        return
    except ValueError:
        pass

    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        addr_info = socket.getaddrinfo(clean_host, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror as e:
        raise SSRFSecurityError(f"Failed to resolve hostname '{clean_host}': {e}") from e

    resolved_ips: list[ipaddress.IPv4Address | ipaddress.IPv6Address] = []
    for _family, _, _, _, sockaddr in addr_info:
        ip_str = sockaddr[0]
        try:
            resolved_ips.append(ipaddress.ip_address(ip_str))
        except ValueError:
            continue

    if not resolved_ips:
        raise SSRFSecurityError(f"No valid IP addresses resolved for hostname '{clean_host}'.")

    for resolved_ip in resolved_ips:
        if is_ip_blocked(resolved_ip):
            raise SSRFSecurityError(
                f"Hostname '{clean_host}' resolved to forbidden IP '{resolved_ip}'."
            )
