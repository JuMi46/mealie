from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from mealie.schema.household.webhook import ReadWebhook
from mealie.services.scheduler.tasks.post_webhooks import post_test_webhook
from tests.utils import api_routes, assert_deserialize, jsonify
from tests.utils.fixture_schemas import TestUser


@pytest.fixture()
def webhook_data():
    return {
        "enabled": True,
        "name": "Test-Name",
        "url": "https://my-fake-url.com",
        "time": "00:00",
        "scheduledTime": datetime.now(UTC),
    }


def test_create_webhook(api_client: TestClient, unique_user: TestUser, webhook_data):
    response = api_client.post(
        api_routes.households_webhooks,
        json=jsonify(webhook_data),
        headers=unique_user.token,
    )
    assert response.status_code == 201


def test_read_webhook(api_client: TestClient, unique_user: TestUser, webhook_data):
    response = api_client.post(
        api_routes.households_webhooks,
        json=jsonify(webhook_data),
        headers=unique_user.token,
    )
    item_id = response.json()["id"]

    response = api_client.get(api_routes.households_webhooks_item_id(item_id), headers=unique_user.token)
    webhook = assert_deserialize(response, 200)

    assert webhook["id"] == item_id
    assert webhook["name"] == webhook_data["name"]
    assert webhook["url"] == webhook_data["url"]
    assert webhook["scheduledTime"] == str(webhook_data["scheduledTime"].astimezone(UTC).time())
    assert webhook["enabled"] == webhook_data["enabled"]


def test_update_webhook(api_client: TestClient, webhook_data, unique_user: TestUser):
    response = api_client.post(
        api_routes.households_webhooks,
        json=jsonify(webhook_data),
        headers=unique_user.token,
    )
    item_dict = assert_deserialize(response, 201)
    item_id = item_dict["id"]

    webhook_data["name"] = "My New Name"
    webhook_data["url"] = "https://my-new-fake-url.com"
    webhook_data["enabled"] = False

    response = api_client.put(
        api_routes.households_webhooks_item_id(item_id),
        json=jsonify(webhook_data),
        headers=unique_user.token,
    )
    updated_webhook = assert_deserialize(response, 200)

    assert updated_webhook["name"] == webhook_data["name"]
    assert updated_webhook["url"] == webhook_data["url"]
    assert updated_webhook["enabled"] == webhook_data["enabled"]


def test_delete_webhook(api_client: TestClient, webhook_data, unique_user: TestUser):
    response = api_client.post(
        api_routes.households_webhooks,
        json=jsonify(webhook_data),
        headers=unique_user.token,
    )
    item_dict = assert_deserialize(response, 201)
    item_id = item_dict["id"]

    response = api_client.delete(api_routes.households_webhooks_item_id(item_id), headers=unique_user.token)
    assert response.status_code == 200

    response = api_client.get(api_routes.households_webhooks_item_id(item_id), headers=unique_user.token)
    assert response.status_code == 404


def test_post_test_webhook(
    monkeypatch: pytest.MonkeyPatch, api_client: TestClient, unique_user: TestUser, webhook_data
):
    # Mock the requests.post to avoid actual HTTP calls
    class MockResponse:
        status_code = 200

    mock_calls = []

    def mock_post(*args, **kwargs):
        mock_calls.append((args, kwargs))
        return MockResponse()

    monkeypatch.setattr("mealie.services.event_bus_service.publisher.requests.post", mock_post)

    # Create a webhook and post it
    response = api_client.post(
        api_routes.households_webhooks,
        json=jsonify(webhook_data),
        headers=unique_user.token,
    )
    webhook_dict = assert_deserialize(response, 201)

    webhook = ReadWebhook(
        id=webhook_dict["id"],
        name=webhook_dict["name"],
        url=webhook_dict["url"],
        scheduled_time=webhook_dict["scheduledTime"],
        enabled=webhook_dict["enabled"],
        group_id=webhook_dict["groupId"],
        household_id=webhook_dict["householdId"],
    )

    test_message = "This is a test webhook message"
    post_test_webhook(webhook, test_message)

    # Verify that requests.post was called with the correct parameters
    assert len(mock_calls) == 1
    args, kwargs = mock_calls[0]

    assert kwargs["json"]["message"]["body"] == test_message
    assert kwargs["timeout"] == 15
    assert args[0] == webhook.url


def test_post_test_timer_webhook_with_parsed_url_and_payload(
    monkeypatch: pytest.MonkeyPatch,
    api_client: TestClient,
    unique_user: TestUser,
):
    class MockResponse:
        status_code = 200

    mock_calls = []

    def mock_post(*args, **kwargs):
        mock_calls.append((args, kwargs))
        return MockResponse()

    monkeypatch.setattr("mealie.services.scheduler.tasks.post_webhooks.requests.post", mock_post)

    create_response = api_client.post(
        api_routes.households_webhooks,
        json={
            "enabled": True,
            "name": "Timer Test",
            "url": "https://example.com/hook?length={length}&message={message}",
            "webhookType": "timer",
            "timerEvent": "updated",
            "isDeepLink": False,
        },
        headers=unique_user.token,
    )
    webhook = assert_deserialize(create_response, 201)

    response = api_client.post(
        f"{api_routes.households_webhooks_item_id_test(webhook['id'])}/timer",
        json={
            "timerId": "timer-test-123",
            "length": "120",
            "message": "hello world",
            "completeTime": "2026-01-01T00:00:00Z",
            "completeTimeInMs": 1767225600000,
        },
        headers=unique_user.token,
    )

    assert response.status_code == 200
    assert len(mock_calls) == 1

    args, kwargs = mock_calls[0]
    assert args[0] == "https://example.com/hook?length=120&message=hello%20world"
    assert kwargs["json"] == {
        "action": "update",
        "timerId": "timer-test-123",
        "length": "120",
        "message": "hello world",
        "recipeLink": "",
        "completeTime": "2026-01-01T00:00:00Z",
        "completeTimeInMs": 1767225600000,
    }
