"""Smoke test: the crew answers GET /, and POST /ask runs both agents with no key, no provider
choice, and no network - and the "no key" answer doesn't just read [stub: ...] silently."""

import os

from fastapi.testclient import TestClient

from main import NO_KEY_MESSAGE, app

client = TestClient(app)


def test_root_answers_200():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ask_answers_with_the_no_key_message_by_default():
    body = client.post("/ask", json={"question": "Why use a crew?"}).json()
    assert body["mode"] == "stub"
    assert body["answer"] == NO_KEY_MESSAGE


def test_anthropic_provider_also_gets_the_no_key_message_with_no_key():
    os.environ["LLM_PROVIDER"] = "anthropic"
    try:
        body = client.post("/ask", json={"question": "Why use a crew?"}).json()
    finally:
        os.environ.pop("LLM_PROVIDER", None)
    assert body["mode"] == "stub"
    assert body["answer"] == NO_KEY_MESSAGE


def test_rejects_an_empty_or_oversized_question():
    assert client.post("/ask", json={"question": ""}).status_code == 422
    assert client.post("/ask", json={"question": "x" * 501}).status_code == 422


def test_works_without_any_api_key():
    assert "OPENAI_API_KEY" not in os.environ
    assert "ANTHROPIC_API_KEY" not in os.environ
