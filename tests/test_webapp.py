from fastapi.testclient import TestClient

from gridiron_edge.webapp import create_app


def test_dashboard_renders():
    app = create_app()
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "Gridiron Edge" in response.text
    assert "viewport" in response.text
    assert "On your phone or iPad" in response.text
    assert "0.0.0.0" in response.text


def test_api_urls_never_lists_bind_all():
    app = create_app()
    client = TestClient(app)
    response = client.get("/api/urls")
    assert response.status_code == 200
    body = response.json()
    assert body["mac"].startswith("http://127.0.0.1:")
    assert "lan_reachable" in body
    for url in body["phone"]:
        assert "0.0.0.0" not in url
        assert "127.0.0.1" not in url
        assert url.startswith("http://")

