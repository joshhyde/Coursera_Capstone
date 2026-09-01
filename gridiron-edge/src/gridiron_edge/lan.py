from __future__ import annotations

import socket

UNUSABLE_BIND_HOSTS = frozenset({"0.0.0.0", "::", "127.0.0.1", "::1", "localhost"})
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})


def discover_ipv4s() -> list[str]:
    found: list[str] = []
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET, socket.SOCK_STREAM):
            ip = info[4][0]
            if _usable_ipv4(ip):
                found.append(ip)
    except OSError:
        pass
    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            probe.connect(("8.8.8.8", 80))
            ip = probe.getsockname()[0]
            if _usable_ipv4(ip):
                found.append(ip)
        finally:
            probe.close()
    except OSError:
        pass
    return list(dict.fromkeys(found))


def phone_urls(
    port: int,
    *,
    ipv4s: list[str] | None = None,
    hostname: str | None = None,
) -> list[str]:
    urls: list[str] = []
    for ip in ipv4s if ipv4s is not None else discover_ipv4s():
        if not _usable_ipv4(ip):
            continue
        urls.append(f"http://{ip}:{port}")
    name = (hostname if hostname is not None else socket.gethostname()).split(".")[0]
    if name and name.lower() not in UNUSABLE_BIND_HOSTS:
        urls.append(f"http://{name}.local:{port}")
    return list(dict.fromkeys(urls))


def bind_reaches_lan(host: str) -> bool:
    """False when the server is bound only to this Mac (phones cannot connect)."""
    return host.strip().lower() not in LOOPBACK_HOSTS


def _usable_ipv4(ip: str) -> bool:
    if ip in UNUSABLE_BIND_HOSTS:
        return False
    if ip.startswith("127.") or ip.startswith("169.254."):
        return False
    return True
