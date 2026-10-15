"""Server-Side Request Forgery (SSRF) protection module."""

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
                           or resolves to a private/loopback/link-local address.

    """
    if not url:
        raise SSRFSecurityError("URL must be a non-empty string.")

    try:
        parsed = urlparse(url)
    except Exception as exc:
        raise SSRFSecurityError(f"Malformed URL '{url}': {exc}") from exc

    scheme = parsed.scheme.lower()
    if scheme not in ALLOWED_SCHEMES:
        raise SSRFSecurityError(f"Blocked scheme '{scheme}'. Only {ALLOWED_SCHEMES} are allowed.")

    if parsed.username or parsed.password:
        raise SSRFSecurityError("URLs containing embedded credentials are not allowed.")

    hostname = parsed.hostname
    if not hostname:
        raise SSRFSecurityError(f"Missing host in URL: '{url}'.")

    # If hostname is directly an IP literal
    try:
        literal_ip = ipaddress.ip_address(hostname)
        if is_ip_blocked(literal_ip):
            raise SSRFSecurityError(
                f"Blocked access to private or reserved IP address: {literal_ip}"
            )
        return
    except ValueError:
        # Not an IP literal, proceed to DNS resolution
        pass

    # Resolve hostname via DNS
    try:
        addr_info = socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise SSRFSecurityError(f"DNS resolution failed for '{hostname}': {exc}") from exc

    resolved_ips: set[ipaddress.IPv4Address | ipaddress.IPv6Address] = set()
    for item in addr_info:
        sockaddr = item[4]
        ip_str = sockaddr[0]
        try:
            resolved_ips.add(ipaddress.ip_address(ip_str))
        except ValueError:
            continue

    if not resolved_ips:
        raise SSRFSecurityError(f"No IP addresses resolved for hostname '{hostname}'.")

    for ip in resolved_ips:
        if is_ip_blocked(ip):
            raise SSRFSecurityError(
                f"Host '{hostname}' resolved to blocked private or loopback IP: {ip}"
            )
