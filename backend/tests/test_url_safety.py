import pytest
from services.url_safety import validate_safe_url, UnsafeUrlError


def test_allows_public_https():
    scheme, host = validate_safe_url("https://www.amazon.co.jp/dp/B0CHR8YHTD", resolve_dns=False)
    assert scheme == "https"
    assert host == "www.amazon.co.jp"


def test_rejects_ftp_scheme():
    with pytest.raises(UnsafeUrlError):
        validate_safe_url("ftp://example.com/file", resolve_dns=False)


def test_rejects_file_scheme():
    with pytest.raises(UnsafeUrlError):
        validate_safe_url("file:///etc/passwd", resolve_dns=False)


def test_rejects_localhost():
    with pytest.raises(UnsafeUrlError):
        validate_safe_url("http://localhost/admin", resolve_dns=False)


def test_rejects_loopback_ip():
    with pytest.raises(UnsafeUrlError):
        validate_safe_url("http://127.0.0.1/", resolve_dns=False)


def test_rejects_aws_metadata_ip():
    with pytest.raises(UnsafeUrlError):
        validate_safe_url("http://169.254.169.254/latest/meta-data/", resolve_dns=False)


def test_rejects_private_ip_10_range():
    with pytest.raises(UnsafeUrlError):
        validate_safe_url("http://10.0.0.1/", resolve_dns=False)


def test_rejects_private_ip_192_range():
    with pytest.raises(UnsafeUrlError):
        validate_safe_url("http://192.168.1.1/", resolve_dns=False)


def test_rejects_ipv6_loopback():
    with pytest.raises(UnsafeUrlError):
        validate_safe_url("http://[::1]/", resolve_dns=False)


def test_rejects_empty_url():
    with pytest.raises(UnsafeUrlError):
        validate_safe_url("", resolve_dns=False)


def test_rejects_url_without_host():
    with pytest.raises(UnsafeUrlError):
        validate_safe_url("http:///path", resolve_dns=False)


def test_rejects_internal_suffix():
    with pytest.raises(UnsafeUrlError):
        validate_safe_url("http://db.internal/", resolve_dns=False)
