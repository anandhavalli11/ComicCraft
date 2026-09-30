from fastapi.testclient import TestClient

from app.main import app


client = TestClient(
    app
)


def test_home_page():

    response = client.get(
        "/"
    )

    assert response.status_code == 200

    assert "ComicCraft" in response.text


def test_health():

    response = client.get(
        "/health"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"


def test_generate_comic():

    payload = {

        "story": (
            "A brave fox explores "
            "an enchanted forest."
        ),

        "character": "Finn",

        "setting": "Enchanted Forest",

        "tone": "adventure",

        "art_style": "cartoon",

        "panel_count": 3
    }

    response = client.post(
        "/generate-comic/json",
        json=payload
    )

    assert response.status_code == 200

    data = response.json()

    assert len(
        data["panels"]
    ) == 3

    assert data["character"] == "Finn"