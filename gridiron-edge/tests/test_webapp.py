from fastapi.testclient import TestClient

from gridiron_edge.webapp import create_app


def test_dashboard_renders():
    app = create_app()
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "Gridiron Edge" in response.text
