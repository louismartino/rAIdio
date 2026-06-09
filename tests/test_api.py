from datetime import date
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies import get_settings
from src.config import Settings
from src.pipeline import PipelineOutcome

TARGET_DATE = date(2026, 6, 8)


@pytest.fixture
def api_client(settings: Settings) -> TestClient:
    get_settings.cache_clear()

    from main import app

    app.dependency_overrides[get_settings] = lambda: settings
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    get_settings.cache_clear()


def test_home_page_loads(api_client: TestClient) -> None:
    response = api_client.get("/")

    assert response.status_code == 200
    assert "Run process" in response.text


def test_run_process_returns_401_when_api_key_is_missing(api_client: TestClient) -> None:
    response = api_client.post("/run-process")

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API key."


def test_run_process_returns_401_when_api_key_is_invalid(api_client: TestClient) -> None:
    response = api_client.post(
        "/run-process",
        headers={"X-API-Key": "wrong-key"},
    )

    assert response.status_code == 401


def test_run_process_runs_pipeline_for_target_date(api_client: TestClient) -> None:
    outcome = PipelineOutcome(status="completed", target_date=TARGET_DATE)

    with patch(
        "main.run_newsletter_process",
        new_callable=AsyncMock,
        return_value=outcome,
    ) as mock_run:
        response = api_client.post(
            f"/run-process?target_date={TARGET_DATE.isoformat()}",
            headers={"X-API-Key": "test-api-key"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "status": "completed",
        "target_date": TARGET_DATE.isoformat(),
        "detail": None,
    }
    mock_run.assert_awaited_once_with(target_date=TARGET_DATE)


def test_run_process_defaults_target_date_to_today(api_client: TestClient) -> None:
    today = date.today()
    outcome = PipelineOutcome(status="no_newsletters", target_date=today)

    with patch(
        "main.run_newsletter_process",
        new_callable=AsyncMock,
        return_value=outcome,
    ) as mock_run:
        response = api_client.post(
            "/run-process",
            headers={"X-API-Key": "test-api-key"},
        )

    assert response.status_code == 200
    mock_run.assert_awaited_once_with(target_date=today)
