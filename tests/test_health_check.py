import requests

from src.graphics_db_server.logging import logger


def test_health_check():
    """
    Tests that the healthcheck endpoint works.
    """
    response = requests.get("http://localhost:2692/healthcheck")
    logger.info(f"Healthcheck response: {response.json()}")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["db"] == "ok"
    assert response.json()["data_exists"] is True


if __name__ == "__main__":
    test_health_check()
