from gridiron_edge.lan import bind_reaches_lan, phone_urls


def test_phone_urls_skip_bind_all_and_loopback():
    urls = phone_urls(
        8787,
        ipv4s=["0.0.0.0", "127.0.0.1", "192.168.1.20"],
        hostname="Mac-mini",
    )
    assert urls == [
        "http://192.168.1.20:8787",
        "http://Mac-mini.local:8787",
    ]


def test_phone_urls_never_suggest_zero_zero():
    urls = phone_urls(8787, ipv4s=["0.0.0.0"], hostname="localhost")
    assert urls == []


def test_phone_urls_skip_link_local():
    urls = phone_urls(8787, ipv4s=["169.254.12.34"], hostname="localhost")
    assert urls == []


def test_phone_urls_still_print_bonjour_when_only_bind_all():
    urls = phone_urls(8787, ipv4s=["0.0.0.0"], hostname="Mac-mini")
    assert urls == ["http://Mac-mini.local:8787"]


def test_bind_reaches_lan():
    assert bind_reaches_lan("0.0.0.0") is True
    assert bind_reaches_lan("192.168.1.20") is True
    assert bind_reaches_lan("127.0.0.1") is False
    assert bind_reaches_lan("localhost") is False
