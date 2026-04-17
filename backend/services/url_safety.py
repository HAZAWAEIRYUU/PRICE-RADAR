"""Safe URL validation for user-supplied competitor URLs.

Rejects URLs that could drive SSRF against the scraper host:
loopback, link-local, multicast, private (RFC1918), IPv6 ULA,
and metadata endpoints. Also rejects schemes other than http/https.

The scraper must never fetch a URL that hasn't been through this
validator — either at write time (product/competitor create/update)
or right before the fetch as a last line of defense.
"""
from __future__ import annotations

import ipaddress
import socket
from typing import Tuple
from urllib.parse import urlparse


class UnsafeUrlError(ValueError):
    """Raised when a URL points at an address we refuse to fetch."""


_ALLOWED_SCHEMES = ("http", "https")

# Hostnames that shouldn't reach the public internet and whose resolution
# we don't want to rely on at all — short-circuit before DNS.
_BLOCKED_HOSTNAME_SUFFIXES = (
    "localhost",
    ".localhost",
    ".local",
    ".internal",
)


def _is_blocked_ip(ip: ipaddress._BaseAddress) -> bool:
    if ip.is_loopback or ip.is_private or ip.is_link_local:
        return True
    if ip.is_multicast or ip.is_reserved or ip.is_unspecified:
        return True
    # AWS / GCP / Azure metadata endpoints resolve to link-local (169.254.169.254)
    # which is already covered by is_link_local, but be explicit.
    if isinstance(ip, ipaddress.IPv4Address) and str(ip) == "169.254.169.254":
        return True
    return False


def validate_safe_url(url: str, *, resolve_dns: bool = True) -> Tuple[str, str]:
    """Validate that `url` is safe for the scraper to fetch.

    Raises UnsafeUrlError on failure. Returns (scheme, host) on success.

    `resolve_dns=True` additionally resolves the hostname and rejects any
    result that maps to a private/loopback/link-local address. Skip only
    in tests.
    """
    if not url or not isinstance(url, str):
        raise UnsafeUrlError("URL is empty")

    parsed = urlparse(url.strip())
    if parsed.scheme.lower() not in _ALLOWED_SCHEMES:
        raise UnsafeUrlError(f"Scheme '{parsed.scheme}' not allowed (only http/https)")

    host = parsed.hostname
    if not host:
        raise UnsafeUrlError("URL has no host")

    host_lower = host.lower()
    for suffix in _BLOCKED_HOSTNAME_SUFFIXES:
        if host_lower == suffix.lstrip(".") or host_lower.endswith(suffix):
            raise UnsafeUrlError(f"Host '{host}' is not externally routable")

    # If the host is a literal IP, check directly (no DNS needed).
    literal_ip = None
    try:
        literal_ip = ipaddress.ip_address(host)
    except ValueError:
        literal_ip = None  # not an IP literal — fall through to DNS check
    if literal_ip is not None:
        if _is_blocked_ip(literal_ip):
            raise UnsafeUrlError(f"Host IP '{host}' is not externally routable")
        return parsed.scheme.lower(), host_lower

    if resolve_dns:
        try:
            infos = socket.getaddrinfo(host, None)
        except socket.gaierror as e:
            raise UnsafeUrlError(f"Cannot resolve host '{host}': {e}")
        for info in infos:
            sockaddr = info[4]
            try:
                ip = ipaddress.ip_address(sockaddr[0])
            except (ValueError, IndexError):
                continue
            if _is_blocked_ip(ip):
                raise UnsafeUrlError(
                    f"Host '{host}' resolves to non-public address {ip}"
                )

    return parsed.scheme.lower(), host_lower
