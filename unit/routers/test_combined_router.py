import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch

from lightbox_api.routers.combined_router import router


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_combined_success_returns_200(client):
    mock_result = {"results": [{"name": "Hyderabad"}]}
    mock_status = 200

    with patch(
        "lightbox_api.routers.combined_router.combined_geocode_reverse_service"
    ) as mock_service:
        mock_service.return_value = (mock_result, mock_status)

        resp = client.get("/combined?street=MG%20Road&locality=Hyderabad")

        assert resp.status_code == 200
        assert resp.json() == mock_result
        mock_service.assert_called_once()


@pytest.mark.parametrize(
    "status_code, service_payload, expected_detail",
    [
        (400, {"detail": "Invalid input"}, "Invalid input"),
        (401, {"detail": "Unauthorized"}, "Unauthorized"),
        (403, {"detail": "Forbidden"}, "Forbidden"),
        (429, {"detail": "Rate limited"}, "Rate limited"),
        (503, {"detail": "Upstream service down"}, "Upstream service down"),
    ],
)
def test_combined_raises_http_exception_when_service_returns_error(
    client, status_code, service_payload, expected_detail
):
    with patch(
        "lightbox_api.routers.combined_router.combined_geocode_reverse_service"
    ) as mock_service:
        mock_service.return_value = (service_payload, status_code)

        resp = client.get("/combined?street=MG%20Road&locality=Hyderabad")

        assert resp.status_code == status_code
        assert resp.json()["detail"] == expected_detail


def test_combined_uses_message_if_detail_missing(client):
    service_payload = {"message": "Expired LightBox key"}
    status_code = 401

    with patch(
        "lightbox_api.routers.combined_router.combined_geocode_reverse_service"
    ) as mock_service:
        mock_service.return_value = (service_payload, status_code)

        resp = client.get("/combined?street=MG%20Road&locality=Hyderabad")

        assert resp.status_code == 401
        assert resp.json()["detail"] == "Expired LightBox key"


def test_combined_returns_default_error_if_no_detail_or_message(client):
    service_payload = {}
    status_code = 503

    with patch(
        "lightbox_api.routers.combined_router.combined_geocode_reverse_service"
    ) as mock_service:
        mock_service.return_value = (service_payload, status_code)

        resp = client.get("/combined?street=MG%20Road&locality=Hyderabad")

        assert resp.status_code == 503
        assert resp.json()["detail"] == "Error"


def test_combined_fastapi_validation_error_for_invalid_type(client):
    resp = client.get("/combined?buffer_distance=abc")
    assert resp.status_code == 422