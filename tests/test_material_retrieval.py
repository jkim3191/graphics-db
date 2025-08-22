import requests

from src.graphics_db_server.logging import logger


def test_material_search(query_text: str):
    """
    Tests material semantic search functionality.
    """
    response = requests.get(
        "http://localhost:8000/api/v0/materials/search",
        params={"query": query_text},
    )
    logger.info(f"Material Query: {query_text}. Response: {response}")
    assert response.status_code == 200
    response_json = response.json()
    assert len(response_json) > 0
    return response_json


if __name__ == "__main__":
    test_material_search("wooden floor")