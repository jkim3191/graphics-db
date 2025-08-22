import requests

from src.graphics_db_server.logging import logger


def test_asset_search(query_text: str):
    """
    Tests graphics asset semantic search functionality.
    """
    response = requests.get(
        "http://localhost:2692/api/v0/assets/search",
        params={"query": query_text},
    )
    logger.info(f"Query: {query_text}. Response: {response}")
    assert response.status_code == 200
    response_json = response.json()
    assert len(response_json) > 0
    return response_json



if __name__ == "__main__":
    test_asset_search("a blue car")
