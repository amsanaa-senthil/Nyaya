from fastapi.testclient import TestClient

import app


def test_collaboration_flow_end_to_end():
    client = TestClient(app.app)
    owner_headers = {"X-User-ID": "owner-test-user"}

    create_response = client.post(
        "/conversations",
        json={
            "title": "Mens rea discussion",
            "tags": ["criminal", "mens-rea"],
            "matter_id": "MAT-001",
            "jurisdiction": "Sri Lanka",
        },
        headers=owner_headers,
    )
    assert create_response.status_code == 200
    conversation_id = create_response.json()["id"]

    message_response = client.post(
        f"/conversations/{conversation_id}/messages",
        json={
            "role": "assistant",
            "content": "Mens rea requires a guilty mind.",
            "citations": [{"pdf_name": "x.pdf", "page": 1}],
            "evidence_score": 0.8,
        },
        headers=owner_headers,
    )
    assert message_response.status_code == 200
    message_key = message_response.json()["message_key"]

    edit_response = client.patch(
        f"/conversations/{conversation_id}/messages/{message_key}",
        json={
            "content": "Mens rea generally refers to the mental element of an offense.",
            "citations": [{"pdf_name": "x.pdf", "page": 2}],
            "evidence_score": 0.85,
        },
        headers=owner_headers,
    )
    assert edit_response.status_code == 200
    assert edit_response.json()["version"] == 2

    share_response = client.post(
        f"/conversations/{conversation_id}/share",
        json={"permission": "comment", "expires_in_hours": 24, "password": "secret"},
        headers=owner_headers,
    )
    assert share_response.status_code == 200
    share_token = share_response.json()["share_token"]

    access_response = client.post(
        f"/shares/{share_token}/access",
        json={"password": "secret"},
        headers={"X-User-ID": "reviewer-test-user"},
    )
    assert access_response.status_code == 200
    assert access_response.json()["permission"] == "comment"

    comment_response = client.post(
        f"/conversations/{conversation_id}/comments",
        json={
            "content": "Please verify paragraph 2 with another authority.",
            "mentions": ["reviewer-test-user"],
            "message_key": message_key,
        },
        headers=owner_headers,
    )
    assert comment_response.status_code == 200

    review_response = client.patch(
        f"/conversations/{conversation_id}/review-status",
        json={"review_status": "approved"},
        headers=owner_headers,
    )
    assert review_response.status_code == 200
    assert review_response.json()["review_status"] == "approved"

    export_response = client.get(
        f"/conversations/{conversation_id}/export",
        headers=owner_headers,
    )
    assert export_response.status_code == 200
    payload = export_response.json()
    assert payload["conversation"]["id"] == conversation_id
    assert len(payload["conversation"]["messages"]) >= 1

    revoke_response = client.post(
        f"/conversations/{conversation_id}/share/{share_token}/revoke",
        headers=owner_headers,
    )
    assert revoke_response.status_code == 200

    denied_access_response = client.post(
        f"/shares/{share_token}/access",
        json={"password": "secret"},
        headers={"X-User-ID": "reviewer-test-user"},
    )
    assert denied_access_response.status_code == 403
