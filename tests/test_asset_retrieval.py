import requests

from src.graphics_db_server.logging import logger


def test_asset_search(query_text: str):
    """
    Tests that we can search for assets.
    """
    response = requests.post(
        "http://localhost:8000/api/v0/assets/search",
        params={"query": query_text},
    )
    logger.info(f"Query: {query_text}. Response: {response}")
    assert response.status_code == 200
    assert len(response.json()) > 0


if __name__ == "__main__":
    test_asset_search("a blue car")
